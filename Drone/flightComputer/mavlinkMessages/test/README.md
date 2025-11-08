These test scripts are used to verify that all MAVLink commands will run successfully.

As a prerequisite, SITL with ArduCopter must be running. All prearm checks must have passed (run SITL, and wait until simulated calibrations are complete).

Note that receiving a `result: 0` indicated success. This is denoted by `MAV_RESULT` in the MAVLink docs.