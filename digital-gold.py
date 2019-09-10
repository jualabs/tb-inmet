import math
N = 5
M = 5
X = [0, 4, 2, 0]
Y = [0, 0, 1, 4]

def solution(N, M, X, Y):
    retorno = 0;
    # verifica o tamanho dos arrays e se o numero de lotes com ouro e par
    if(len(X) == len(Y) and len(X)%2 == 0):
        K = len(X)
        X.sort()
        retorno += (X[int(K/2)] - X[int((K/2)-1)])
        Y.sort()
        retorno += (Y[int(K/2)] - Y[int((K/2)-1)])
    return retorno

print(solution(N, M, X, Y))