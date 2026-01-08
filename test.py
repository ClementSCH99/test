import u6
from time import sleep

d = u6.U6()

# 1) Préparer les timers
d.configIO(
    NumberTimersEnabled=1,
    TimerCounterPinOffset=0
)

# 2) Définir la fréquence du timer
d.configTimerClock(
    TimerClockBase=3,   # Horloge interne
    TimerClockDivisor=255
)

# 3) Activer le timer en mode PWM 8-bit
d.getFeedback(
    u6.TimerConfig(timer=0, TimerMode=0)
)

# 4) Boucle PWM : 0%, 50%, 100%
for val in range(0, 10000000, 10000):
    d.getFeedback(
        u6.Timer(timer=0, Value=val, UpdateReset=True)
    )
    sleep(1)

d.close()
