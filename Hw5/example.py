"""Repeatable headless trajectory: python -B -m Hw5.example."""

from . import Parameters, State, step


def main():
    parameters = Parameters(mass=2.0, dt=0.01)
    state = State(position=(1, 2, 3), velocity=(2, 3, -1))
    force = (4, 6, -2)
    for _ in range(100):
        state = step(state, parameters, force)
    print("HW5 Part 1: 3D point-mass free flight (SI)")
    print(f"steps={state.step_count}, time={state.time:.9f} s, mass={parameters.mass:g} kg")
    print("position (m):", tuple(round(x, 9) for x in state.position))
    print("velocity (m/s):", tuple(round(v, 9) for v in state.velocity))
    print("continuous position at 1 s (m): (4.0, 1.595, 1.5)")
    print("expected Euler position bias (m): (0.01, -0.03405, -0.005)")


if __name__ == "__main__":
    main()
