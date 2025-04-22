# based on the paper https://www.researchgate.net/publication/260014821_Neural_Network_based_Inverse_Kinematics_Solution_for_Trajectory_Tracking_of_a_Robotic_Arm
# I will record 1000 samples.
# These samples will be random angles for the shoulder, omoplate, rotate, and wrist.
# For collecting the data I will wait for 5 seconds to give the arms enough time to position.
# Then, using Mediapipe, I will record their positions. Which will be the labels for the already mentioned random angles.

# After that, I will train a FNN (input:positions, 1 hidden layer 100 neurons, output:angles) using hyperbolic tangent. (These are the settings from the paper)


# TODO:

# Data Collection

# Model Definition

# Training and Evaluation Functions

