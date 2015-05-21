# reporting-producers
Reporting Producers - collecting data on anything and everything for eRSA reporting purposes.

Ease of use currently trumps performance concerns, so everything is dumped out as JSON for now. (The JSON is consumed by a [Dropwizard](http://www.dropwizard.io) API which pushes it into [Kafka](http://kafka.apache.org).)

