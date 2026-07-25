from predictor import predict_cases

prediction = predict_cases(
    state="Uttar Pradesh",
    district="Lucknow",
    year=2025,
    crime_type="Robbery",
    chargesheeted=900,
    convictions=450,
    population=7100000,
)

print(prediction)