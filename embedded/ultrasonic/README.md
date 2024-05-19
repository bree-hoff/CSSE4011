# Ultrasonic Sensor Integration Manual

<pre>

         Y
                            - 0 cm
      |      |
------+------+------        - 25 cm
      |      |        X
------+------+------        - 70 cm 
      |      |

      ^      ^      ^
    70cm   25cm    0cm
</pre>

## Conditions:

    x < 25 cm   ---> 1
    x > 70 cm   ---> -1
    25 < x < 70 ---> 0
    
    y < 25 cm   ---> 1
    y > 70 cm   ---> -1
    25 < y < 70 ---> 0

## Outputs

    Each m5 will send a packet via MQTT to the base node in the format: "a b"
    Where a = x or y, and b = -1, 0, 1.

    -1 = backward along the respective axis
    0 = stationary along the respective axis
    1 = forward along the respective axis

## MQTT

IP Address for mosquitto connection: 	
10.180.153.18
    


    
