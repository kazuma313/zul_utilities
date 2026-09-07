"""
-> dalam grup k orang, berapa probabilitas minimal dua orang punya hari ulang
tahun sama? Jalankan simulasi untuk berbagai k dan bandingkan dengan rumus
analitisnya.

Input:
    k (int) - jumlah orang dalam grup.
    trials (int) - jumlah simulasi yang dijalankan, default 10000.
    seed (int | None) - random seed untuk hasil yang reproducible, default None.
Output: (float) - estimasi probabilitas (0.0 - 1.0) minimal dua orang berbagi
    hari ulang tahun yang sama.
    
pesudocode:

set random seed
set count

for trials:
    for k:
        set random (0, 365)
    if have the same value in list:
        count =+ number of same value
        
return count/trials

"""

import random

def simulate_birthday_paradox(k: int, trials: int = 10000, seed: int | None = None) -> float:
    """
    Estimate the probability that at least two people in a group of k share a
    birthday, via Monte Carlo simulation.

    Args:
        k (int): Number of people in the group.
        trials (int): Number of simulation trials. Defaults to 10000.
        seed (int | None): Random seed for reproducibility. Defaults to None.

    Returns:
        float: Estimated probability in [0.0, 1.0].

    Raises:
        ValueError: If k is negative or trials is not positive.
    """
    
    random.seed(seed)
    count = 0
    
    if k < 0:
        raise ValueError("k must be non-negative")

    if trials <= 0:
        raise ValueError("trials must be positive")
    
    for _ in range(trials):
        list_person_birthday = [] 
        for _ in range(k):
            list_person_birthday.append(random.randint(1, 365))
        
        unique_birthday = set(list_person_birthday)
        if len(unique_birthday) != len(list_person_birthday):
            count += 1
            
    return count/trials


if __name__ == "__main__":
    print(simulate_birthday_paradox(k=23, trials=10000, seed=42))
