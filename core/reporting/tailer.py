#!/usr/bin/env python

# pylint: disable=broad-except

import os
import glob
import sqlite3
import collections
from reporting.utilities import getLogger
from reporting.collectors import IDataSource

log = getLogger(__name__)

class Tailer(IDataSource):
    def __init__(self, config):
        self.__db_path=config['db_path']
        self.__max_line_number=getattr(config, 'max_line_number', 1000)
        self.__interval=0
        self.__check_new_file_interval=10
        self.__tracker={}
        self.__init_tracker(self.__db_path)
        
    def __init_tracker(self, db_path):
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE IF NOT EXISTS tail_tracker(path VARCHAR(256) UNIQUE, \
                        inode int, filename TEXT, mtime int, size int, line_count int)")
            conn.commit()
            cursor = conn.cursor()
            all_rows=cursor.execute("SELECT path, inode, filename, mtime, size, line_count FROM tail_tracker").fetchall()
            for row in all_rows:
                self.__tracker[row[0]]={"inode":row[1], "filename":row[2], "mtime": row[3], "size": row[4], "line_count": row[5]}
                file_handle=open(row[2], 'r')
                jump_lines(file_handle, row[5])
        except Exception as e:
            # Roll back any change if something goes wrong
            conn.rollback()
            log.exception(e)
        finally:
            conn.close()
    
    def __update_tracker(self, path):
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("INSERT OR REPLACE INTO tail_tracker VALUES ('%s', %d, %d, '%s', %d)" % 
                         (path, self.__tracker[path]['inode'], self.__tracker[path]['mtime'], self.__tracker[path]['filename'], self.__tracker[path]['line_count']))
            conn.commit()
        except Exception as e:
            # Roll back any change if something goes wrong
            conn.rollback()
            log.exception(e)
        finally:
            conn.close()

    def find_new_file(self, path):
        tracker=self.__tracker[path]
        new_file_inode=-1
        latest_modified_time=-1
        found_new_file=False
        for file in glob.glob(path):
            fstat=os.stat(file)
            if fstat.st_mtime>latest_modified_time:
                latest_modified_time=fstat.st_mtime
        if found_new_file:
            self.__update_tracker(path)
            
    def add_new_tracker(self, path, collect_history_data=False):
        file_list=[]
        for file in glob.glob(path):
            file_st=os.stat(file)
            file_list.append({'filename': file, "inode": file_st.st_ino, "mtime": file_st.st_mtime, "size": file_st.st_size})
        if len(file_list)==0:
            return
        file_list.sort(key=lambda file: file['mtime'])
        if collect_history_data:
            log.debug("current file stat %s"%file_st)
            self.__tracker[path]={"inode":file_list[0]['inode'], 
                                            "filename":file_list[0]['filename'], 
                                            "mtime": file_list[0]['mtime'], 
                                            "size": file_list[0]['size'], 
                                            "line_count": 0,
                                            "file_handle": open(file_list[0]['filename'], 'r')}
        else:
            log.debug("current file stat %s"%file_st)
            file_handle=open(file_list[-1]['filename'], 'r')
            self.__tracker[path]={"inode":file_list[-1]['inode'], 
                                            "filename":file_list[-1]['filename'], 
                                            "mtime": file_list[-1]['mtime'], 
                                            "size": file_list[-1]['size'], 
                                            "line_count": count_line_number(file_handle)}
        self.__add_tracker(path)
        
        
    def get_data(self, config=None):
        log.debug(config)
        if config is None:
            return None
        # path is not tracked, add it
        if not config['path'] in self.__tracker:
            collect_history_data=False
            if 'collect_history_data' in config:
                collect_history_data=config['collect_history_data']
            self.add_new_tracker(config['path'], collect_history_data)
        # something is wrong with the path, return None
        if not config['path'] in self.__tracker:
            return None
        path=config['path']
        if hasattr(self.__tracker[path],'cache') and len(self.__tracker[path]['cache'])>0:
            return self.__tracker[path]['cache']
        if self.__interval>=self.__check_new_file_interval:
            self.__interval=0
            self.find_new_file(path)
        else:
            self.__interval+=1
        return self.get_lines(self.__tracker[path]['file_handle'])
    
    def success(self, config):
        if config is None:
            return
        path=config['path']
        self.__tracker[path]['cache']=[]
        self.__tracker[path]['line_count']=self.__tracker[path]['line_count']+len(lines)
        self.__update_db(path)
    
    def fail(self, config):
        if config is None:
            return
        path=config['path']
    
    def get_lines(self, file):
        lines_got=0
        lines=collections.deque([])
        while True:
            line=file.readline()
            if not line:
                break
            lines.append(line)
            lines_got+=1
            if lines_got>=self.__max_line_number:
                break
        return lines

def jump_lines(file, line_number):
    current_line=0
    for i, l in enumerate(file):
        current_line+=1
        if current_line>=line_number:
            break
    log.debug("file %s is at line %d (position %d)" % (file.name, i, file.tell()))
    
def count_line_number(file):
    for i, l in enumerate(file):
        pass
    log.debug("file %s is at line %d (position %d)" % (file.name, i, file.tell()))
    return i