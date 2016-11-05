Emitters
========

InfluxDb
----------

InfluxDb pushes the metric data into your configure host setting.
You can also specifiy tags for your metric data, like hostgroup or role. The hostname and
the unit of your metric is always part of your tags. Example config could look like

    InfluxDbPush:
      host: my-influxdb.example.com
      port: 8086
      user: illuminati
      password: s3cre3t
      dbname: illuminati
      tags:
        serverrole: webserver
        region    : eu

CloudWatch
----------

To use CloudWatch, you must have ~/.boto set up with your AWS Identity and Secret keys.
You must also then specify a namespace for your metrics, and optionally additional dimensions.
If you are running sauron on an EC2 instance, it will automatically include the instance-id
in the dimensions.

[__CloudWatch Alarms__](http://aws.amazon.com/documentation/cloudwatch/) can now be baked into
the configuration of the CloudWatch emitter. For example, suppose you want to watch to make 
sure that an apache process is running at all times. You could configure a ProcMetric to match
the appropriate process configuration. Then, you'd add an __action__ to CloudWatch, and an 
__alarm__ that executes that action when certain conditions on that metric are reached:

	# For example, we support CloudWatch
	CloudWatch:
    namespace: ...
    actions:
        emailAdmin:
            - {endpoint: my@email.com}
    alarms:
        serverDied:
            description: Oh noes! Apache fell over!
            metric: apache-count
            threshold: 0
            comparison: <=
            alarm:
                - emailAdmin
            insufficient_data:
                - emailAdmin

	# Counts the number of apache processes
	apache:
		module: ProcMetric

The CloudWatch Alarm API is perhaps a little complex, but we wanted our configuration to reflect
it closely. You can provide the actions to take when the alarm is in the INSUFFICIENT\_DATA state,
(which can be a good indication that either monitoring or the machine died), ALARM, and OK (which
doesn't necessarily seem like a useful state, but it's available in the API). You can also include
the dimensions across which you'd like to gather data, but we imagine you'd often like to watch
on a per-instance basis.

Twitter
-------

We also support Twitter, mostly as a lark. It's kind of cludge-y -- you have to make a Twitter app,
save the consumer key and consumer secret in the configuration file, and then once you've authorized
the app, then save your account's access key and access secret for the app. Also, be aware that 
__Twitter limits the number of posts a user can push to 1000 per day__, so if you have a lot of
metrics to monitor, you have to sample very sparsely. One metric once a minute is already above that
limit (1440 per day)

Extensibility
=============

To write your own emitter, simply inherit from `sauron.emitters.Emitter`. Your emitter will be
initialized with the options associated with it in the configuration file:

	def __init__(self, url, timeout=5, **kwargs):
		# Push data to this particular endpoint

Once metrics are collected, the `metrics` method of your class will be called with a dictionary
dictionaries provided by each of the metrics:

	def metrics(self, metrics):
		for name, dictionary in metrics:
			results = dictionary.get('results', {})
			for stat, value in results:
				print 'Received %s => %s from metric %s' % (stat, repr(value), name)

Your emitter should capture all internal errors and only raise a `EmitterException` in the event
of a legitimate failure.
