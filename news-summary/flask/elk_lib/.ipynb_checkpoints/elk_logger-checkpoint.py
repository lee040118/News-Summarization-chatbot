import logging
import logstash

'''
#################################################################################
                    SET LOG FORMAT
#################################################################################
'''
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s' , datefmt='%Y-%m-%d:%H:%M:%S')


'''
#################################################################################
                    Werkzeug LOGGER SETTING
#################################################################################
'''
werkzeug = logging.getLogger('werkzeug')
# werkzeug.disabled = True

'''
#################################################################################
                    MAIN LOGGER SETTING
#################################################################################
'''
web_logger_logstash = logging.getLogger('web logger')
web_logger_logstash.setLevel(logging.DEBUG)
stash = logstash.TCPLogstashHandler('211.38.19.229',5001,version=1)
stash.setFormatter(formatter)
web_logger_logstash.addHandler(stash)
# web_logger_logstash.disabled = True

'''
#################################################################################
                    Stream LOGGER SETTING
#################################################################################
'''
web_logger_stream = logging.getLogger('web stream')
web_logger_stream.setLevel(logging.DEBUG)
stream = logging.StreamHandler()
stream.setFormatter(formatter)
web_logger_stream.addHandler(stream)
# web_logger_stream.disabled = True