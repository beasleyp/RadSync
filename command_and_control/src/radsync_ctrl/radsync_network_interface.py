# The RadSync program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

'''
This module contains the structure for all the messages that should be sent
between the Arestor Radar and the RadSync system. It also contains the structure
for all the messages that should be sent between RadSync nodes.

Any changes to the comminication should be made to this document, NOT inside
the command and control modules of either system. This will allow the interface
to be easily updated without the requirement for updating multiple code bases.
'''


from . import main_script
from . import trigger_control

    
Delimiter = '$'

# Arestor message prefixes
Arestor_trig_prefix = 'arest_trig_req'

# Radsync master node message prefixes
RadSync_master_trig_prefix = 'master_trig_req'
RadSync_master_trig_ack_prefix = 'radsync_trig_ack'
RadSync_master_trig_valid_prefix = 'radsync_trig_validity'

# RadSync slave node message prefixes
RadSync_slave_trig_ack_prefix = 'slave_trig_ack'
RadSync_slave_trig_valid_prefix = 'slave_trig_valid'

# RadSync gps quality strings 
not_connected = "not connected"
not_tracking_gps = "not tracking gps"
poor_gps_sync = "poor time synchronisation"# PPSOUT - PPSREF error > 20ns 
nominal_gps_sync = "nominal time synchronisation" # PPSOUT - PPSREF error < 20ns 
good_gps_sync = "good time synchronisation" # PPSOUT - PPSREF error < 10ns 


def arestor_decode_message(message):
    '''
    this function should be used to decode all messaged received by the Arestor 
    system - only use in arestor command and control system 
    '''    
    #split the message header/prefix from the message body
    message = message.split(Delimiter,-1)

    if message[0] == RadSync_master_trig_ack_prefix:
        '''
        decode trigger acknowledgement from radsync master node
        '''
        unix_trigger_deadline = message[1]
        node_0_gps_quality = message[2]
        node_1_gps_quality = message[3]
        node_2_gps_quality = message[4]
        print("RadSync Trigger Request Acknowledgement \n")
        print("Unix trigger deadline" +  str(unix_trigger_deadline) + "\n")
        for x in range(2,len(message)):
            print("Node " + str(x) + " : " + message[x] + "\n")
       
    if message[0] == RadSync_master_trig_valid_prefix:
        '''
        decode trigger validity message from radsync master node
        '''
        node_0_trig_validity = message[1]
        node_1_trig_validity = message[2]
        node_2_trig_validity = message[3]
        print("RadSync Trigger Validity Message Received \n")
        for x in range(1,len(message)):
            print("Node " + str(x) + " : " + message[x] + "\n")
       
            
        
def radsync_decode_message(message):
    '''
    this function should be used to decode all messaged received by RadSync 
    system nodes - only use in radsync command and control system 
    '''    
    #split the message header/prefix from the message body
    message = message.split(Delimiter,-1)
    

    if (message[0] == Arestor_trig_prefix):
        '''
        ddecode trigger request from arestor 
        '''
        trigger_type = message[1]
        trigger_delay = message[2]
        print("Trigger request received from Arestor \n")
        print("Trigger type :" + trigger_type + "  Trigger Delay :" + trigger_delay)
        main_script.handle_arestor_trigger_request(trigger_type,trigger_delay)
    
 
    if (message[0] == RadSync_master_trig_prefix):
        '''
        decode trigger request from radsync master node
        '''
        unix_trigger_deadline = message[1]
        trigger_id = message[2]
        print("Trigger request received from Master \n")
        print("Trigger type :" + str(trigger_id) + "  Unix trigger deadline :" + unix_trigger_deadline)
        
        # initiate trigger in the trigger subsystem
        main_script.handle_slave_trigger_request(unix_trigger_deadline,trigger_id)
        
        
    
    if (message[0] == RadSync_slave_trig_ack_prefix):
        '''
        decode trigger acknowledgement message from radsync slave node
        '''
        node_number = message[1]
        gps_sync_state = message[2]
        print("Trigger Ack from Node " + str(node_number) + " : " + gps_sync_state)
        main_script.handle_slave_trigger_ack(node_number,gps_sync_state)
    
    if (message[0] == RadSync_slave_trig_valid_prefix):
        '''
        decode validity message from slave radsync node
        '''
        node_number = message[1]
        trigger_validity = message[2]
        print("Trigger validity from Node " + str(node_number) + " : " + trigger_validity) 
        main_script.handle_slave_trigger_validity(node_number,trigger_validity)
  


      
        
'''
Functions to be used by the ARESTOR system to encode messages
'''

def create_arestor_trig_req_message(trigger_type, trigger_delay):
    '''
    function to create arestor trigger request message - only to be used by arestor command and cotrol script
    '''
    message = Arestor_trig_prefix + Delimiter + trigger_type + Delimiter + trigger_delay
    return message


'''
Functions to be used by the RADSYNC MASTER node to encode 
'''

def create_arestor_trig_req_response(unix_trigger_deadline, node_0_gps_quality, node_1_gps_quality=not_connected, node_2_gps_quality=not_connected):
    '''
    fucntion to create response message to send to arestor - only to be 
    used by RadSync
    prefix-node_0_gps_quality-node_1_gps_quality-node_2_gps_quality
    '''
    message = RadSync_master_trig_ack_prefix + Delimiter + unix_trigger_deadline + Delimiter + node_0_gps_quality + node_1_gps_quality + node_2_gps_quality
    return message 

def create_arestor_trig_validity_message(node_0_trig_validity, node_1_trig_validity, node_2_trig_validity):
    '''
    fucntion to create message to send to arestor with each nodes trigger 
    validity - only to be used by radsync
    '''
    message = RadSync_master_trig_valid_prefix + Delimiter + node_0_trig_validity + Delimiter + node_1_trig_validity + Delimiter + node_2_trig_validity
    return message
    
def create_radsync_trig_req_message(unix_trigger_deadline, trigger_id):
    '''
    fucntion to create message to send to slave radsync nodes to request 
    trigger - only to be used by radsync
    '''
    message = RadSync_master_trig_prefix + Delimiter + str(int(unix_trigger_deadline)) + Delimiter + str(trigger_id)
    return message



'''
Functions to be used by the RADSYNC SLAVE node to encode messages
'''

def create_radsync_trig_ack_message(node_number, gps_sync_state):
    '''
    fucntion to create message to send to master radsync nodes with trigger 
    validity - only to be used by radsync.
    '''
    message = RadSync_slave_trig_valid_prefix + Delimiter + node_number + Delimiter + gps_sync_state
    return message

def create_radsync_trig_validity_message(node_number, trigger_validity):
    '''
    fucntion to create message to send to master radsync nodes with trigger 
    validity - only to be used by radsync.
    '''
    message = RadSync_slave_trig_valid_prefix + Delimiter + node_number + Delimiter + trigger_validity
    return message
