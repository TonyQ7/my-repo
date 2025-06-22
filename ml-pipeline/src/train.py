import joblib
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier


def train_model():
    data = load_iris()
    X, y = data.data, data.target
    clf = RandomForestClassifier()
    clf.fit(X, y)
    joblib.dump(clf, '../models/model.joblib')
    print('Model trained and saved')

if __name__ == '__main__':
    train_model()
