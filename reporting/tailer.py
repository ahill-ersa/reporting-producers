#!/usr/bin/env python

# pylint: disable=broad-except

import os
import glob
import sqlite3
import collections
import errno
from reporting.utilities import getLogger
from reporting.collectors import IDataSource

log = getLogger(__name__)

class Tailer(IDataSource):
    def __init__(self, config):
        self.__db_path=config['db_path']
        self.__max_line_number=config.get('max_line_number', 1000)
        self.__interval=0
        self.__sizehint = config.get('sizehint', 1048576)
        self.__check_new_file_interval=10
        self.__tracker={}
        self.__init_tracker()
        
    def __init_tracker(self):
        conn = None
        try:
            conn = sqlite3.connect(self.__db_path)
            conn.execute("CREATE TABLE IF NOT EXISTS tail_tracker(path VARCHAR(256) UNIQUE, \
                        inode int, filename TEXT, mtime int, size int, line_count int)")
            conn.commit()
            cursor = conn.cursor()
            all_rows=cursor.execute("SELECT path, inode, filename, mtime, size, line_count FROM tail_tracker").fetchall()
            for row in all_rows:
                path=row[0]
                self.__tracker[path]={"inode":row[1], "filename":row[2], "mtime": row[3], "size": row[4], "line_count": row[5]}
                file_handle=open(row[2], 'r')
                if row[5]>0:
                    self.jump_lines(file_handle, row[5])
                self.__tracker[path]['file_handle']=file_handle
        except Exception as e:
            # Roll back any change if something goes wrong
            conn.rollback()
            log.exception(e)
        finally:
            if conn:
                conn.close()
    
    def __update_tracker(self, path):
        conn = None
        try:
            conn = sqlite3.connect(self.__db_path)
            conn.execute("INSERT OR REPLACE INTO tail_tracker VALUES ('%s', %d, '%s', %d, %d, %d)" % 
                         (path, self.__tracker[path]['inode'], self.__tracker[path]['filename'], self.__tracker[path]['mtime'], 
                          self.__tracker[path]['size'], self.__tracker[path]['line_count']))
            conn.commit()
        except Exception as e:
            # Roll back any change if something goes wrong
            conn.rollback()
            log.exception(e)
        finally:
            if conn:
                conn.close()

    def find_new_file(self, path):
        tracker=self.__tracker[path]
        current_file=tracker['filename']
        current_st=None
        need_to_update=False
        try:
            current_st=os.stat(current_file)
        except EnvironmentError as err:
            if err.errno == errno.ENOENT:
                log.info('file %s removed' % current_file)
                tracker['file_handle'].close()
            else:
                log.exception("can't stat file %s"%current_file)
                return
        if tracker['file_handle'].closed:
            file_list=self.query_files(path)
            if len(file_list)==0:
                log.error("No file found for path %s"%path)
                return
            log.info("open newest file, stat %s"%file_list[-1])
            self.__tracker[path]={"inode":file_list[-1]['inode'], 
                                    "filename":file_list[-1]['filename'], 
                                    "mtime": file_list[-1]['mtime'], 
                                    "size": file_list[-1]['size'], 
                                    "line_count": 0,
                                    "file_handle": open(file_list[-1]['filename'], 'r')}
            need_to_update=True
        else:
            if tracker['inode']!=current_st.st_ino:
                log.info('file %s rotated' % current_file)
                # need to read for the last time before closing
                lines = self.get_lines(tracker['file_handle'])
                if len(lines)>0:
                    self.__tracker[path]['cache']=lines
                tracker['file_handle'].close()
                tracker['file_handle']=open(tracker['filename'], 'r')
                tracker['inode']=current_st.st_ino
                tracker['mtime']=current_st.st_mtime
                tracker['size']=current_st.st_size
                tracker['line_count']=0
                need_to_update=True
            else:
                file_list=self.query_files(path)
                log.debug("current file %s; current location %d ; file size %d "% (current_file, tracker['file_handle'].tell(), current_st.st_size))
                if tracker['file_handle'].tell()>=current_st.st_size:
                    for file in file_list:
                        if file['filename']!=current_file and file['mtime']>current_st.st_mtime:
                            # found a new file
                            log.info("reached end of file %s, track a new file %s"%(current_file, file['filename']))
                            tracker['filename']=file['filename']
                            tracker['inode']=file['inode']
                            tracker['mtime']=file['mtime']
                            tracker['size']=file['size']
                            tracker['line_count']=0
                            tracker['file_handle'].close()
                            tracker['file_handle']=open(tracker['filename'], 'r')
                            need_to_update=True
                            break
        if need_to_update:
            self.__update_tracker(path)

    def query_files(self, path):            
        file_list=[]
        for file in glob.glob(path):
            file_st=os.stat(file)
            file_list.append({'filename': file, "inode": file_st.st_ino, "mtime": int(file_st.st_mtime), "size": file_st.st_size})
        file_list.sort(key=lambda file: file['mtime'])
        return file_list
    
    def add_new_tracker(self, path, collect_history_data=False):
        file_list=self.query_files(path)
        if len(file_list)==0:
            return
        if collect_history_data:
            log.debug("current file stat %s"%file_list[0])
            self.__tracker[path]={"inode":file_list[0]['inode'], 
                                            "filename":file_list[0]['filename'], 
                                            "mtime": file_list[0]['mtime'], 
                                            "size": file_list[0]['size'], 
                                            "line_count": 0,
                                            "file_handle": open(file_list[0]['filename'], 'r')}
        else:
            log.debug("current file stat %s"%file_list[-1])
            file_handle=open(file_list[-1]['filename'], 'r')
            self.__tracker[path]={"inode":file_list[-1]['inode'], 
                                            "filename":file_list[-1]['filename'], 
                                            "mtime": file_list[-1]['mtime'], 
                                            "size": file_list[-1]['size'], 
                                            "line_count": self.count_line_number(file_handle),
                                            "file_handle": file_handle}
        self.__update_tracker(path)
        
        
    def get_data(self, config=None):
        log.debug(config)
        if config is None or not 'path' in config:
            log.error("config is none or doesn't have path: %s" % config)
            return None
        # path is not tracked, add it
        path=config['path']
        if not path in self.__tracker:
            log.debug('path %s is not tracked, create it' % path)
            collect_history_data=False
            if 'collect_history_data' in config:
                collect_history_data=config['collect_history_data']
            self.add_new_tracker(path, collect_history_data)
        # something is wrong with the path, return None
        if not path in self.__tracker:
            log.error('unable to create tracker for path %s' % path)
            return None
        if 'cache' in self.__tracker[path] and len(self.__tracker[path]['cache'])>0:
            log.debug('found data in cache for path %s, return cache' % path)
            return self.__tracker[path]['cache']
        if self.__interval>=self.__check_new_file_interval:
            log.debug('time to find new file for path %s' % path)
            self.__interval=0
            self.find_new_file(path)
        else:
            self.__interval+=1
        if 'cache' in self.__tracker[path] and len(self.__tracker[path]['cache'])>0:
            log.debug('last bit of data in cache for path %s, return cache' % path)
            return self.__tracker[path]['cache']
        if self.__tracker[path]['file_handle'] is None or self.__tracker[path]['file_handle'].closed:
            log.debug('unable to find a new file for path %s, return empty' % path)
            return []
        lines = self.get_lines(self.__tracker[path]['file_handle'])
        self.__tracker[path]['cache']=lines
        return lines
    
    def success(self, config):
        if config is None:
            return
        path=config['path']
        log.debug("successfully sent log for %s" % path)
        no_lines=len(self.__tracker[path]['cache'])
        del self.__tracker[path]['cache']
        self.__tracker[path]['line_count']=self.__tracker[path]['line_count']+no_lines
        self.__update_tracker(path)
    
    def fail(self, config):
        if config is None:
            return
        path=config['path']
        log.debug("failed to send log for %s, try again later" % path)
    
    def get_lines(self, file):
        lines_got=0
        lines=collections.deque([])
        while True:
            buffer=file.readline()
            if not buffer:
                break
            lines.append(buffer)
            lines_got+=1
            if lines_got>=self.__max_line_number:
                break
        return lines

    def jump_lines(self, file, line_number):
        current_line=0
        while True:
            line=file.readline()
            if not line:
                break
            current_line+=1
            if current_line>=line_number:
                break
        log.debug("file %s is at line %d (position %d)" % (file.name, current_line, file.tell()))
    
    def count_line_number(self, file):
        line_number=0
        while True:
            buffer=file.readlines(self.__sizehint)
            if not buffer:
                break
            line_number+=len(buffer)
        log.debug("file %s is at line %d (position %d)" % (file.name, line_number, file.tell()))
        return line_number