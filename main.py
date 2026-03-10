import numpy as np
from scipy.io import loadmat
import matplotlib.pyplot as plt

# -----------------------------
# Global parameters
# -----------------------------
lambda1 = 0.01
lambda2 = 0.1


# -----------------------------
# Pattern Learning
# -----------------------------
def patternLearn(data, data2, beta1, beta2, beta3, beta4):

    alpha = 0.01
    max_iter = 1000

    R = data
    R2 = data2

    N, T = R.shape

    P = np.random.rand(N, N)

    for Iter in range(max_iter):

        PDP = CalPDP(P, R, R2, beta1, beta2, beta3, beta4)

        P -= alpha * PDP

        if Iter % 5 == 0:
            alpha *= 0.95

        if Iter % 200 == 0:
            print(f"Iter {Iter} | pdp={np.sum(np.abs(PDP)):.2f}")

    return P


# -----------------------------
# Vectorized gradient
# -----------------------------
def CalPDP(P, R, R2, beta1, beta2, beta3, beta4):

    N, T = R.shape

    PDP = np.zeros((N, N))

    for t in range(T - 4):

        term2 = (
            beta1 * R2[:, t]
            + beta2 * R2[:, t + 1]
            + beta3 * R2[:, t + 2]
            + beta4 * R2[:, t + 3]
        )

        pred = P @ term2

        error = pred - R[:, t + 4]

        PDP += 2 * np.outer(error, term2)

    PDP += 2 * lambda1 * P + lambda2 * np.sign(P)

    return PDP


# -----------------------------
# Prediction → Label
# -----------------------------
def turnRealtoLabel(realPredict):

    realPredict = np.tanh(realPredict)

    row, col = realPredict.shape

    predictLabel = np.zeros((row, col))

    for j in range(col):

        pos = realPredict[:, j] > 0

        if np.sum(pos) == 0:
            continue

        mean_val = np.mean(realPredict[pos, j])
        std_val = np.std(realPredict[pos, j])

        threshold = mean_val + std_val

        threshold = max(threshold, 0.98)

        predictLabel[:, j] = (realPredict[:, j] > threshold).astype(int)

    return predictLabel


# -----------------------------
# F1 Metrics
# -----------------------------
def FMeasure(truth, predict):

    TP = np.sum((truth == 1) & (predict == 1))
    TN = np.sum((truth == 0) & (predict == 0))
    FP = np.sum((truth == 0) & (predict == 1))
    FN = np.sum((truth == 1) & (predict == 0))

    accuracy = (TP + TN) / truth.size

    precision = TP / (TP + FP + 1e-6)

    recall = TP / (TP + FN + 1e-6)

    F1 = 2 * precision * recall / (precision + recall + 1e-6)

    return accuracy, precision, recall, F1


# -----------------------------
# MAIN
# -----------------------------
def main():

    data_mat = loadmat("hotspot14.mat")

    areaWeek = data_mat["subzoneHotspotWeek14"]
    areaPotential = data_mat["subzoneHotspotPotential14"]

    win = 5
    fromWeek = 0
    toWeek = 52

    data = areaWeek[:, fromWeek:toWeek]
    data2 = areaPotential[:, fromWeek:toWeek]

    m, n = data.shape

    horizon = toWeek - fromWeek + 1 - win

    P3D = np.zeros((m, m, horizon))
    P3D_best = np.zeros_like(P3D)

    metricBest = np.zeros((horizon, 4))
    betaBest = np.zeros((horizon, 4))

    PredOneStep = np.zeros((m, horizon))
    PredBest = np.zeros((m, horizon))

    for i in range(5, horizon):

        print(f"\nWeek window {i}")

        for beta1 in np.arange(0.2, 0.91, 0.03):
            for beta2 in np.arange(0.1, 0.51, 0.03):
                for beta3 in np.arange(0.1, 0.31, 0.03):
                    for beta4 in np.arange(0.1, 0.31, 0.03):

                        P = patternLearn(
                            data[:, i:i+win],
                            data2[:, i:i+win],
                            beta1, beta2, beta3, beta4
                        )

                        P3D[:, :, i] = P

                        input_vec = (
                            beta1 * data2[:, i + win - 1]
                            + beta2 * data2[:, i + win - 2]
                            + beta3 * data2[:, i + win - 3]
                            + beta4 * data2[:, i + win - 4]
                        )

                        PredOneStep[:, i] = P @ input_vec

                        labelPred = turnRealtoLabel(
                            PredOneStep[:, i:i+1]
                        )

                        a, p, r, f1 = FMeasure(
                            data[:, i+win:i+win+1],
                            labelPred
                        )

                        if f1 > metricBest[i, 3]:

                            metricBest[i] = [a, p, r, f1]
                            P3D_best[:, :, i] = P
                            PredBest[:, i] = PredOneStep[:, i]

                            betaBest[i] = [beta1, beta2, beta3, beta4]

    plt.plot(metricBest[:,2])
    plt.title("Recall")
    plt.show()


if __name__ == "__main__":
    main()