# Ultrasonic Sensor Integration Manual

<pre>

         Y
                            - 0 cm
      |      |
------+------+------        - 40 cm
      |      |        X
------+------+------        - 70 cm 
      |      |

      ^      ^      ^
    70cm   40cm    0cm
</pre>

## Conditions:

    x < 40 cm   ---> 1
    x > 80 cm   ---> -1
    40 < x < 80 ---> 0
    
    y < 40 cm   ---> 1
    y > 80 cm   ---> -1
    40 < y < 80 ---> 0

## Outputs

    Each m5 will send a packet via MQTT to the base node in the format: "a b"
    Where a = x or y, and b = -1, 0, 1.

    -1 = backward along the respective axis
    0 = stationary along the respective axis
    1 = forward along the respective axis

## MQTT

IP Address for mosquitto connection: 	
10.180.153.18
    


    
