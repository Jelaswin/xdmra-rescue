# Model Card: Custom ML Priority Predictor

## Intended Use
This machine learning model predicts the priority level (`low`, `medium`, `high`, `critical`) of disaster incidents to assist control-room officers in decision-making. 

## Inputs and Outputs
**Inputs:** 
Structured numeric and categorical variables including: `incident_type`, `severity`, `affected_people`, `injured_people`, `trapped_people`, `vulnerable_people`, `children_count`, `elderly_count`, and `waiting_time_hours`.

**Output:**
- `priority_level` (predicted class)
- `confidence` (probability of the predicted class)
- `class_probabilities` (probabilities for all 4 classes)

## Dataset Type
**SYNTHETIC DATA.** The model is currently trained on a purely synthetic, rule-generated dataset designed to approximate theoretical disaster management logic. It is *not* trained on real historical data.

## Evaluation Metrics
The model is primarily evaluated on **Macro F1-score** to ensure balanced performance across all priority classes, alongside Accuracy, Macro Precision, and Macro Recall.

## Limitations
- The model lacks real-world edge cases.
- It is limited to the predefined structured fields; it does not process unstructured text logs or real-time voice reports.

## Bias and Safety Concerns
Because the data is synthetic, the model's biases directly reflect the programmatic rules used to generate it. Vulnerable populations might be over/under-weighted depending on real-world contexts that this prototype cannot perceive. 

## Human-in-the-Loop Requirement & Non-Autonomous Dispatch
**WARNING:** This model must NEVER be used to automatically dispatch teams. The ML output is strictly for *decision support*. The human officer remains the final authority in confirming priority levels and approving any team allocation.
