# wastemanagement-the-software-prototype
 IoT-Based Smart Waste Management System. A full-stack simulation monitoring bin weight and fill-levels using ESP32 &amp; MQTT to optimize waste collection.

## Advanced capabilities added
- Reproducible simulation controls (bin count + random seed + regenerate)
- Predictive analytics per bin (`Predicted_Fill_24h (%)`, `Predicted_Status_24h`)
- Priority scoring to rank bins for dispatch (`Priority_Score`)
- Operations insights:
  - KPI for bins likely to become critical within 24 hours
  - Top-priority dispatch queue
  - Area-level risk chart by ward
  - Optimized route distance estimate (km) for RED-bin collections
