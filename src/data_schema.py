from typing import List, Optional, Union
from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float


class UserData(BaseModel):
    """
    Data model representing a user.

    Attributes:
        customerID (str): The unique identifier of the customer.
        gender (str): Whether the customer is a male or a female.
        SeniorCitizen (int): Whether the customer is a senior citizen or not (1, 0).
        Partner (str): Whether the customer has a partner or not (Yes, No).
        Dependents (str): Whether the customer has dependents or not (Yes, No).
        tenure (int): Number of months the customer has stayed with the company.
        PhoneService (str): Whether the customer has a phone service or not (Yes, No).
        MultipleLines (str): Whether the customer has multiple lines or not (Yes, No, No phone service).
        InternetService (str): Customer’s internet service provider (DSL, Fiber optic, No).
        OnlineSecurity (str): Whether the customer has online security or not (Yes, No, No internet service).
        OnlineBackup (str): Whether the customer has online backup or not (Yes, No, No internet service).
        DeviceProtection (str): Whether the customer has device protection or not (Yes, No, No internet service).
        TechSupport (str): Whether the customer has tech support or not (Yes, No, No internet service).
        StreamingTV (str): Whether the customer has streaming TV or not (Yes, No, No internet service).
        StreamingMovies (str): Whether the customer has streaming movies or not (Yes, No, No internet service).
        Contract (str): The contract term of the customer (Month-to-month, One year, Two year).
        PaperlessBilling (str): Whether the customer has paperless billing or not (Yes, No).
        PaymentMethod (str): The customer’s payment method (Electronic check, Mailed check, Bank transfer (automatic), Credit card (automatic)).
        MonthlyCharges (float): The amount charged to the customer monthly.
        TotalCharges (float): The total amount charged to the customer.
    """

    customerID: str
    gender: str
    SeniorCitizen: int
    Partner: str
    Dependents: str
    tenure: int
    PhoneService: str
    MultipleLines: str
    InternetService: str
    OnlineSecurity: str
    OnlineBackup: str
    DeviceProtection: str
    TechSupport: str
    StreamingTV: str
    StreamingMovies: str
    Contract: str
    PaperlessBilling: str
    PaymentMethod: str
    MonthlyCharges: float
    TotalCharges: float


class ChurnData(UserData):
    """
    Data model representing a user with churn information.

    Inherits all attributes from UserData and adds:
        Churn (str): Whether the customer churned or not (Yes or No).
    """

    Churn: str


Base = declarative_base()


class TelecomUsers(Base):
    """
    SQLAlchemy model for the TelecomUsers table.

    Attributes:
        __tablename__ (str): The name of the table in the database.
        customerID (Column): The unique identifier of the customer, primary key.
        gender (Column): The gender of the customer.
        SeniorCitizen (Column): Whether the customer is a senior citizen or not (1, 0).
        Partner (Column): Whether the customer has a partner or not (Yes, No).
        Dependents (Column): Whether the customer has dependents or not (Yes, No).
        tenure (Column): Number of months the customer has stayed with the company.
        PhoneService (Column): Whether the customer has a phone service or not (Yes, No).
        MultipleLines (Column): Whether the customer has multiple lines or not (Yes, No, No phone service).
        InternetService (Column): Customer’s internet service provider (DSL, Fiber optic, No).
        OnlineSecurity (Column): Whether the customer has online security or not (Yes, No, No internet service).
        OnlineBackup (Column): Whether the customer has online backup or not (Yes, No, No internet service).
        DeviceProtection (Column): Whether the customer has device protection or not (Yes, No, No internet service).
        TechSupport (Column): Whether the customer has tech support or not (Yes, No, No internet service).
        StreamingTV (Column): Whether the customer has streaming TV or not (Yes, No, No internet service).
        StreamingMovies (Column): Whether the customer has streaming movies or not (Yes, No, No internet service).
        Contract (Column): The contract term of the customer (Month-to-month, One year, Two year).
        PaperlessBilling (Column): Whether the customer has paperless billing or not (Yes, No).
        PaymentMethod (Column): The customer’s payment method (Electronic check, Mailed check, Bank transfer (automatic), Credit card (automatic)).
        MonthlyCharges (Column): The amount charged to the customer monthly.
        TotalCharges (Column): The total amount charged to the customer.
        Churn (Column): Whether the customer churned or not (Yes or No).
    """

    __tablename__ = "TelecomUsers"
    customerID = Column(String, primary_key=True, index=True)
    gender = Column(String, index=True)
    SeniorCitizen = Column(Integer)
    Partner = Column(String)
    Dependents = Column(String)
    tenure = Column(Integer)
    PhoneService = Column(String)
    MultipleLines = Column(String)
    InternetService = Column(String)
    OnlineSecurity = Column(String)
    OnlineBackup = Column(String)
    DeviceProtection = Column(String)
    TechSupport = Column(String)
    StreamingTV = Column(String)
    StreamingMovies = Column(String)
    Contract = Column(String)
    PaperlessBilling = Column(String)
    PaymentMethod = Column(String)
    MonthlyCharges = Column(Float)
    TotalCharges = Column(Float)
    Churn = Column(String)


class ResponseModel(BaseModel):
    """
    Response model for API responses.

    Attributes:
        status (str): The status of the response (e.g., "Success" or "Failed").
        cached (bool): Indicates whether the response was retrieved from cache.
        response (Union[dict, list]): The actual response data, which can be a dictionary or a list.
    """

    status: str
    cached: bool
    response: Union[dict, list]


class TrainRequest(BaseModel):
    """
    Request model for training job initiation.

    Attributes:
        s3_path (Optional[Union[str, None]]): The S3 path to the training data.
    """

    s3_path: Optional[Union[str, None]] = None


class TrainResponse(BaseModel):
    """
    Response model for training job initiation.

    Attributes:
        message (str): The message indicating the status of the training job initiation.
    """

    message: str


class StatusRequest(BaseModel):
    """
    Request model for checking the status of a training job.

    Attributes:
        training_job_name (str): The name of the training job.
    """

    training_job_name: str


class StatusResponse(BaseModel):
    """
    Response model for the status of a training job.

    Attributes:
        training_job_status (str): The status of the training job.
    """

    training_job_status: str


class InferenceRequest(BaseModel):
    """
    Request model for making inferences.

    Attributes:
        training_job_name (str): The name of the training job to use for inference.
        input_data (List[UserData]): The input data for which to make predictions.
    """

    training_job_name: str
    input_data: List[UserData]


class InferenceResponse(BaseModel):
    """
    Response model for inference results.

    Attributes:
        prediction (List[ChurnData]): The predictions made by the model.
    """

    prediction: List[ChurnData]
