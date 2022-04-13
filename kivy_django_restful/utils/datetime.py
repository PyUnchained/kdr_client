# decompyle3 version 3.8.0
# Python bytecode 3.8.0 (3413)
# Decompiled from: Python 3.8.12 (default, Jan 15 2022, 18:39:47) 
# [GCC 7.5.0]
# Embedded file name: /home/tatenda/workspace/kdr_package/kdr_client/kivy_django_restful/utils/date_time.py
# Compiled at: 2022-03-21 13:05:17
# Size of source mod 2**32: 453 bytes
Instruction context:
   
 L.   8        12  LOAD_GLOBAL              datetime
                  14  LOAD_ATTR                datetime
                  16  LOAD_METHOD              strptime
                  18  LOAD_FAST                'date_str'
                  20  LOAD_FAST                'date_format'
                  22  CALL_METHOD_2         2  ''
                  24  POP_BLOCK        
->                26  ROT_TWO          
                  28  POP_TOP          
                  30  RETURN_VALUE     
                32_0  COME_FROM_FINALLY    10  '10'
import datetime
from kivy_django_restful.config import settings

def str_to_date--- This code section failed: ---

 L.   6         0  LOAD_GLOBAL              settings
                2  LOAD_ATTR                REMOTE_DATE_FORMAT
                4  GET_ITER         
              6_0  COME_FROM            44  '44'
              6_1  COME_FROM            40  '40'
                6  FOR_ITER             46  'to 46'
                8  STORE_FAST               'date_format'

 L.   7        10  SETUP_FINALLY        32  'to 32'

 L.   8        12  LOAD_GLOBAL              datetime
               14  LOAD_ATTR                datetime
               16  LOAD_METHOD              strptime
               18  LOAD_FAST                'date_str'
               20  LOAD_FAST                'date_format'
               22  CALL_METHOD_2         2  ''
               24  POP_BLOCK        
               26  ROT_TWO          
               28  POP_TOP          
               30  RETURN_VALUE     
             32_0  COME_FROM_FINALLY    10  '10'

 L.   9        32  POP_TOP          
               34  POP_TOP          
               36  POP_TOP          

 L.  10        38  POP_EXCEPT       
               40  JUMP_BACK             6  'to 6'
               42  END_FINALLY      
               44  JUMP_BACK             6  'to 6'
             46_0  COME_FROM             6  '6'

 L.  12        46  LOAD_GLOBAL              settings
               48  LOAD_ATTR                REMOTE_DATETIME_FORMAT
               50  GET_ITER         
             52_0  COME_FROM            90  '90'
             52_1  COME_FROM            86  '86'
               52  FOR_ITER             92  'to 92'
               54  STORE_FAST               'date_format'

 L.  13        56  SETUP_FINALLY        78  'to 78'

 L.  14        58  LOAD_GLOBAL              datetime
               60  LOAD_ATTR                datetime
               62  LOAD_METHOD              strptime
               64  LOAD_FAST                'date_str'
               66  LOAD_FAST                'date_format'
               68  CALL_METHOD_2         2  ''
               70  POP_BLOCK        
               72  ROT_TWO          
               74  POP_TOP          
               76  RETURN_VALUE     
             78_0  COME_FROM_FINALLY    56  '56'

 L.  15        78  POP_TOP          
               80  POP_TOP          
               82  POP_TOP          

 L.  16        84  POP_EXCEPT       
               86  JUMP_BACK            52  'to 52'
               88  END_FINALLY      
               90  JUMP_BACK            52  'to 52'
             92_0  COME_FROM            52  '52'

 L.  18        92  LOAD_FAST                'date_str'
               94  RETURN_VALUE     
               -1  RETURN_LAST      

Parse error at or near `ROT_TWO' instruction at offset 26
