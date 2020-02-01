{
backends: ['/opt/statsd-utils/statsd-elasticsearch-backend-0.4.2/lib/elasticsearch'],
 //debug: true,
 statsd_host: "localhost",
 elasticsearch: {
     port:          {{ pillar['elasticsearch']['http_port'] }},
     host:          "{{ pillar['elasticsearch']['network_host'] }}",
     path:          "/",
     indexPrefix:   "statsd",
     indexTimestamp: "day",     //for index statsd-2015.01.01
     countType:     "counter",
     timerType:     "timer",
     timerDataType: "timer_data",
     gaugeDataType: "gauge",
     formatter:     "default_format"
  }
}
