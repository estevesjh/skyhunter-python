from skyhunter import IoptronMount
from config import port

# Example usage
mount = IoptronMount(port)

# make sure the telescope is unparked
mount.unpark()

direction = str(input("Enter the direction to slew (left/right) or (up/down): "))
steps = int(input("Enter the number of seconds to slew: "))
nsteps = int(input("Enter the number of steps: "))

mount.set_arrow_speed(9)
for i in range(nsteps):
    print(f"---- Slew to the {direction} for {steps} seconds: {i}")
    # setattr(mount, f"slew_{direction}", steps)
    # run the function mount.slew_{direction}(steps)
    getattr(mount, f"slew_{direction}")(steps)

    # mount.slew_left(steps)
    mount.get_system_state(verbose=False)
    mount.get_current_alt_az()
    print("")
    # print("---------------------------------------------    ")