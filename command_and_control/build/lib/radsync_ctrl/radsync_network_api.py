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



    
Delimiter = '-'
Arestor_trig_prefix = 'arest_trig_req'
RadSync_master_trig_prefix = 'master_trig_req'
RadSync_slave_trig_resp_prefix = 'slave_trig_resp'
RadSync_slave_trig_valid_prefix = 'slave_trig_valid'

   
    def decode_message(message):
        '''
        this function should be used to decode all messaged sent between 
        RadSync and Arestor and between RadSync nodes it is agnotic to if the 
        device is Arestor, or a master or slave radsync 
        node
        '''
        global Delimeter,Arestor_trig_prefix
        #split the message header/prefix from the message body
        message = message.split(Delimeter,-1)
        
        # if message from arestor command and control
        if (message[0] == Arestor_trig_prefix):
            trigger_type = message[1]
            trigger_delay = message[2]
            #TODO include call here to send trigger request to trigger module
        
        # if message from radsync master node 
        if (message[0] == RadSync_master_trig_prefix):
            epoch_trigger_time = message[1]
            trigger_id = message[2]
            #TODO include call here to setup trigger in trigger module
            
        
        if (message[0] == RadSync_slave_trig_resp_prefix):
            pass
        
        if (message[0] == RadSync_slave_trig_valid_prefix):
            node_index = message[1]
            trigger_validity = message[2]
        
            
        
        
    
    # function to create arestor trigger request message - only to be used by arestor command and cotrol script
    def create_arestor_trig_req_message(trigger_type, trigger_delay):
        global Delimiter, Arestor_trig_prefix
        message = Arestor_trig_prefix + Delimeter + trigger_type + Delimeter + trigger_delay
        return message

    
    
    def create_arestor_trig_req_response():
        '''
        fucntion to create response message to send to arestor - only to be 
        used by RadSync 
        '''
   
    def create_arestor_trig_validity_message():
        '''
        fucntion to create message to send to arestor with each nodes trigger 
        validity - only to be used by radsync
        '''
        

        
    def create_radsync_trig_req_message(epoch_trigger_time, trigger_id):
        '''
        fucntion to create message to send to slave radsync nodes to request 
        trigger - only to be used by radsync
        '''
        global Delimiter, Arestor_trig_prefix
        message = RadSync_master_trig_prefix + Delimeter + trigger_time + Delimeter + trigger_id
        return message

    
    def create_radsync_trig_req_message(node_index, trigger_validity):
        '''
        fucntion to create message to send to master radsync nodes with trigger 
        validity - only to be used by radsync.
        '''
        global Delimiter, Arestor_trig_prefix
        message = RadSync_slave_trig_valid_prefix + Delimeter + node_index + Delimeter + trigger_validity
        return message
