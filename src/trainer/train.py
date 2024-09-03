import os
import pandas as pd
import joblib
from sklearn.compose import make_column_transformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def preprocess_data(df):
    """
    Preprocess the input DataFrame by scaling continuous features and encoding categorical features.

    This function takes a DataFrame, scales the continuous columns using StandardScaler,
    and encodes the categorical columns using OneHotEncoder. The fitted transformer is saved
    to a specified path.

    Args:
        df (pd.DataFrame): The input DataFrame to preprocess.

    Returns:
        np.ndarray: The transformed feature matrix.

    Raises:
        Exception: If there is an error during preprocessing.
    """
    try:
        categorical_cols = [
            "gender",
            "SeniorCitizen",
            "Partner",
            "Dependents",
            "PhoneService",
            "MultipleLines",
            "InternetService",
            "OnlineSecurity",
            "OnlineBackup",
            "DeviceProtection",
            "TechSupport",
            "StreamingTV",
            "StreamingMovies",
            "Contract",
            "PaperlessBilling",
            "PaymentMethod",
        ]
        continuous_cols = ["tenure", "MonthlyCharges", "TotalCharges"]
        transformer = make_column_transformer(
            (StandardScaler(), continuous_cols),
            (OneHotEncoder(handle_unknown="ignore"), categorical_cols),
        )
        transformer.fit(df)
        X = transformer.transform(df)
        transformer_output_path = os.path.join("/opt/ml/model", "transformer.joblib")
        joblib.dump(transformer, transformer_output_path)

        return X
    except Exception as e:
        logger.error(f"Error in preprocessing data: {e}")
        raise


if __name__ == "__main__":
    """
    Main script to load data, preprocess it, train a RandomForest model, and save the model.

    This script is intended to be run in a SageMaker training job. It loads the training data from
    a specified path, preprocesses the data, trains a RandomForestClassifier, and saves the trained
    model and the preprocessing transformer to the specified output paths.

    Raises:
        Exception: If there is an error during any step of the process.
    """
    try:
        input_data_path = os.path.join("/opt/ml/input/data/train", "input.csv")
        logger.info(f"Loading data from {input_data_path}")
        df = pd.read_csv(input_data_path)

        df = df.drop("customerID", axis=1)
        df.TotalCharges = pd.to_numeric(df.TotalCharges, errors="coerce")
        df.dropna(inplace=True)

        # Preprocess data
        logger.info("Preprocessing data")
        X = preprocess_data(df)
        y = df["Churn"].values

        # Train model
        logger.info("Training model")
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)

        # Save model
        model_output_path = os.path.join("/opt/ml/model", "model.joblib")
        logger.info(f"Saving model to {model_output_path}")
        joblib.dump(model, model_output_path)

    except Exception as e:
        logger.error(f"Training job failed: {e}")
        raise
