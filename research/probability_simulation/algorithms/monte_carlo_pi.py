"""
-> Monte Carlo Estimasi Pi
Estimasi nilai pi dengan random sampling titik dalam persegi dan hitung
proporsi yang jatuh dalam lingkaran seperempat.

Input:
    n_samples (int) - jumlah titik random yang di-sample.
    seed (int | None) - random seed, default None.
Output: (float) - estimasi nilai pi.

pseudocode:
rumus luas persegi = (2 * r) * (2 * r) = 4r^2
rumus luas lingkaran = phi * r ^ 2  

peluang bola masuk lingkaran = luas lingkaran / luas persegi = phi / 4

phi = 4 * (jumlah titik lingkaran / jumlah keseluruhan titik)

koordinate = (x, y)

mencari jarak titik (phytagoras) = x^2 + y^2

jika jarak titik <= 1 = didalam lingkaran
jika jarak titik > 1 = diluar lingkaran 

"""
import random

def estimate_pi(n_samples: int, seed: int | None = None) -> float:
    """
    Estimate the value of pi using Monte Carlo sampling of points in a unit
    square, based on the proportion that fall inside the quarter circle.

    Args:
        n_samples (int): Number of random points to sample.
        seed (int | None): Random seed for reproducibility. Defaults to None.

    Returns:
        float: Estimated value of pi.

    Raises:
        ValueError: If n_samples is not positive.
    """
    in_circle = 0
    if n_samples <= 0:
        raise ValueError("n_samples must be positive")
    
    random.seed(seed)
    
    for _ in range(n_samples):
        coordinate = (random.uniform(-1, 1), random.uniform(-1, 1))
        distance = coordinate[0]**2 + coordinate[1]**2
        
        # print(distance)
        
        if distance <= 1:
            in_circle += 1
        
    phi=  4 * (in_circle / n_samples)

    return phi
    


if __name__ == "__main__":
    print(estimate_pi(n_samples=9999999, seed=42))
