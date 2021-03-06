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
from . import trigger_control # comment out when used in Arestor Command & Control

    
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
not_connected = "Not connected"
not_tracking_gps = "Not tracking gps"
poor_gps_sync = "Poor time synchronisation"# PPSOUT - PPSREF error > 20ns 
nominal_gps_sync = "Nominal time synchronisation" # PPSOUT - PPSREF error < 20ns 
good_gps_sync = "Good time synchronisation" # PPSOUT - PPSREF error < 10ns 


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
        print("\nRadSync Trigger Request Acknowledgement")
        #print("Unix trigger deadline: " +  str(unix_trigger_deadline))
        for x in range(2,len(message)):
            print("  Node " + str(x-2) + " : " + message[x])
       
    if message[0] == RadSync_master_trig_valid_prefix:
        '''
        decode trigger validity message from radsync master node
        '''
        node_0_trig_validity = message[1]
        node_1_trig_validity = message[2]
        node_2_trig_validity = message[3]
        print("\nRadSync Trigger Validity Message Received")
        for x in range(1,len(message)):
            print("  Node " + str(x-1) + " : " + message[x])
       
            
        
def radsync_decode_message(message):
    '''
    this function should be used to decode all messaged received by RadSync 
    system nodes - only use in radsync command and control system 
    '''    
    #split the message header/prefix from the message body
    message = message.split(Delimiter,-1)
    

    if (message[0] == Arestor_trig_prefix):
        '''
        decode trigger request from arestor 
        '''
        trigger_type = message[1]
        trigger_delay = message[2]
        print("\nTrigger request received from Arestor")
        print("  Trigger type :" + trigger_type + "\n  Trigger Delay :" + trigger_delay)
        if trigger_type == 'radar':
            trigger_type = 3 #1
        if trigger_type == 'freq':
            trigger_type = 4
        main_script.handle_arestor_trigger_request(int(trigger_type),float(trigger_delay))
    
 
    if (message[0] == RadSync_master_trig_prefix):
        '''
        decode trigger request from radsync master node
        '''
        unix_trigger_deadline = float(message[1])
        trigger_duration = int(message[2])
        trigger_id = int(message[3])
        print("\nTrigger request received from Master")
        print("  Trigger type :" + str(trigger_id) + "\n  Trigger duration :" + str(trigger_duration) + "\n" + "\n  Unix trigger deadline :" + str(unix_trigger_deadline) + "\n")
        
        # initiate trigger in the trigger subsystem
        main_script.handle_slave_trigger_request(unix_trigger_deadline, trigger_duration, trigger_id)
        
        
    
    if (message[0] == RadSync_slave_trig_ack_prefix):
        '''
        decode trigger acknowledgement message from radsync slave node
        '''
        node_number = message[1]
        gps_sync_state = message[2]
        print("\nTrigger Ack from Node " + str(node_number) + " : " + gps_sync_state)
        main_script.handle_slave_trigger_ack(node_number,gps_sync_state)
    
    if (message[0] == RadSync_slave_trig_valid_prefix):
        '''
        decode validity message from slave radsync node
        '''
        node_number = message[1]
        trigger_validity = message[2]
        print("\nTrigger validity from Node " + str(node_number) + " : " + trigger_validity)
        main_script.handle_slave_trigger_validity(node_number,trigger_validity)
  


      
        
'''
Functions to be used by the ARESTOR system to encode messages
'''

def create_arestor_trig_req_message(trigger_type, trigger_delay):
    '''
    function to create arestor trigger request message - only to be used by arestor command and cotrol script
    '''
    message = Arestor_trig_prefix + Delimiter + str(trigger_type) + Delimiter + str(trigger_delay)
    return message


'''
Functions to be used by the RADSYNC MASTER node to encode 
'''

def create_arestor_trig_req_response(gps_unix_trigger_deadline, node_0_gps_quality, node_1_gps_quality=not_connected, node_2_gps_quality=not_connected):
    '''
    function to create response message to send to arestor - only to be 
    used by RadSync
    GPS time is 18s ahead of UTC; therefore unix_time_stamp has 18s removed to account for this
    '''
    utc_unix_trigger_deadline = float(gps_unix_trigger_deadline) - 18
    message = RadSync_master_trig_ack_prefix + Delimiter + str(utc_unix_trigger_deadline) + Delimiter + str(node_0_gps_quality) + Delimiter + str(node_1_gps_quality) + Delimiter + str(node_2_gps_quality)
    print(message)
    return message 

def create_arestor_trig_validity_message(node_0_trig_validity, node_1_trig_validity, node_2_trig_validity):
    '''
    fucntion to create message to send to arestor with each nodes trigger 
    validity - only to be used by radsync
    '''
    message = RadSync_master_trig_valid_prefix + Delimiter + str(node_0_trig_validity) + Delimiter + str(node_1_trig_validity) + Delimiter + str(node_2_trig_validity)
    return message
    
def create_radsync_trig_req_message(unix_trigger_deadline, trigger_duration, trigger_id):
    '''
    fucntion to create message to send to slave radsync nodes to request 
    trigger - only to be used by radsync
    '''
    message = RadSync_master_trig_prefix + Delimiter + str(int(unix_trigger_deadline))  + Delimiter + str(trigger_duration) + Delimiter + str(trigger_id)
    return message



'''
Functions to be used by the RADSYNC SLAVE node to encode messages
'''

def create_radsync_trig_ack_message(node_number, gps_sync_state):
    '''
    fucntion to create message to send to master radsync nodes with trigger 
    validity - only to be used by radsync.
    '''
    message = RadSync_slave_trig_ack_prefix + Delimiter + str(node_number) + Delimiter + str(gps_sync_state)
    return message

def create_radsync_trig_validity_message(node_number, trigger_validity):
    '''
    fucntion to create message to send to master radsync nodes with trigger 
    validity - only to be used by radsync.
    '''
    message = RadSync_slave_trig_valid_prefix + Delimiter + str(node_number) + Delimiter + str(trigger_validity)
    return message
