import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer

# Loading and preprocessing the data , the data is in csv format with two columns text and label
# In the dataset there are three types of labels spam,ham and scam we will convert them to binary labels spam/scam as 1 and ham as 0
# We will use tfidf vectorizer to convert the text data to numerical data
def load_and_preprocess(DATA_PATH, MAX_FEATURES):
    df = pd.read_csv(DATA_PATH)
    df["label"] = df["label"].apply( lambda x: 1 if str(x).lower() in ["spam", "scam", "1"] else 0)
    df = df.dropna()
    X_train, X_test, y_train, y_test = train_test_split(df["text"],df["label"], test_size=0.4) # add if model doesnt work random_state=21
    vectorizer = TfidfVectorizer(max_features=MAX_FEATURES)
    X_train_vec = vectorizer.fit_transform(X_train) 
    X_test_vec = vectorizer.transform(X_test) 
    return X_train_vec, X_test_vec, y_train.values, y_test.values, vectorizer
