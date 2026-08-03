import numpy as np
rng = np.random.default_rng(7)

def C(delta, m):
    W, W2 = m.sum(), (m**2).sum()
    S, Q = (m*delta).sum(), (m*delta**2).sum()
    return S*np.sqrt(W/(W2*Q))

N, n = 400000, 20
print(f"{'case':34s} {'mean':>7s} {'sd':>7s} {'P(|C|>2.58)':>12s}")
for name, gen, mgen in [
    ("gaussian walk, unit mass",      lambda: rng.normal(0,1,n),            lambda: np.ones(n)),
    ("gaussian walk, lognormal vol",  lambda: rng.normal(0,1,n),            lambda: rng.lognormal(0,1,n)),
    ("student-t(3) walk, unit mass",  lambda: rng.standard_t(3,n),          lambda: np.ones(n)),
    ("GARCH-ish (vol clustered)",     None,                                  lambda: np.ones(n)),
    ("price scaled x1000 (scale inv)",lambda: rng.normal(0,1,n)*1000,       lambda: np.ones(n)),
]:
    out = np.empty(N)
    for i in range(N):
        if name.startswith("GARCH"):
            s = np.empty(n); v = 1.0; d = np.empty(n)
            for k in range(n):
                d[k] = rng.normal(0, np.sqrt(v)); v = 0.05 + 0.10*d[k]**2 + 0.85*v
            delta = d
        else:
            delta = gen()
        out[i] = C(delta, mgen())
    print(f"{name:34s} {out.mean():7.3f} {out.std():7.3f} {np.mean(np.abs(out)>2.58):12.4f}")

# identity checks
d = rng.normal(0,1,n); m = rng.lognormal(0,1,n)
W = m.sum(); w = m/W
neff = 1/ (w**2).sum(); vbar = (w*d).sum(); u = np.sqrt((w*d**2).sum())
ell = np.sqrt(neff)*u; Deff = neff*vbar
print("\nidentity  C == sqrt(neff)*vbar/u :", np.isclose(C(d,m), np.sqrt(neff)*vbar/u))
print("identity  C == Deff/ell          :", np.isclose(C(d,m), Deff/ell))
print("identity  Phi == C^2/neff <= 1   :", (C(d,m)**2/neff) <= 1)
print("bound     |C| <= sqrt(neff)      :", abs(C(d,m)) <= np.sqrt(neff))
# equal-mass closed form: C = D / sqrt(sum d^2)
d2 = rng.normal(0,1,n)
print("equalmass C == D/L2(steps)       :", np.isclose(C(d2,np.ones(n)), d2.sum()/np.sqrt((d2**2).sum())))
