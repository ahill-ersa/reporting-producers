[![Build Status](https://travis-ci.org/eResearchSA/reporting-producers.svg?branch=master)](https://travis-ci.org/eResearchSA/reporting-producers)

# reporting-producers
Reporting Producers - collecting data on anything and everything for eRSA reporting purposes.

### Example config file

```yaml
global:
    # you can overwrite the hostname here
    hostname: alias.host.name

collector:
    cpu:
        input:
            type: file
            path: "/proc/stat"
            frequency: 10
        parser:
            type: class
            name: reporting.plugins.linux.CPUParser
        output: buffer
        metadata:
            schema: linux.cpu
            version: 1
```

### Sections

- global
- collector
- trailer: if input type is a trailer, database file name and related information
- logging: logging related

### Attributes of a `collector`

- input:

  - type: define the type of source from which information is collected
    - file: single file
    - command: an executable which generates information for collecting
    - trailer: a direcotry with a tracking sqlite db to remeber which file was the last processed

### Generated JSON structure:

```json
{
  "schema": "the type of this record (e.g. zfs.kstat)",
  "version": "the version of the above type (e.g. 1, 2, 3, ...)",
  "id": "a uuid for this record",
  "timestamp": "seconds since epoch (integer)",
  "hostname": "host which generated this record (e.g. blah.ersa.edu.au)",
  "session": "a uuid for this session (session = a single execution of the producer)",
  "data": {
    "a" : "dictionary",
    "containing" : [ "the", "relevant", "data" ],
    "ps" : {
      "you" : "can nest it",
      "if" : "desired"
    }
  }
}
```

Example:

```json
{
  "schema": "iostat.osx",
  "version": 1,
  "id": "c924dafc-e9ed-47ca-93d9-3ede92516391",
  "session": "b88ab7e6-86f6-40cf-9c2d-c8a5a8a8da1b",
  "timestamp": 1428374685,
  "hostname": "transmat.local",
  "data": {"kb/t": 110.78, "tps": 23, "mb/s": 2.47}
}
```
