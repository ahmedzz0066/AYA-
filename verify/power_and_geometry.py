import numpy as np
rng = np.random.default_rng(11)
def C(d,m):
    W,W2=m.sum(),(m**2).sum(); S,Q=(m*d).sum(),(m*d**2).sum()
    return S*np.sqrt(W/(W2*Q))
N=200000
# 1) exact empirical quantiles of the null (unit mass), several n
print("null |C| quantiles (unit mass):")
print(f"{'n':>4} {'q95':>6} {'q99':>6} {'q999':>6} {'sqrt(n) cap':>11}")
for n in (10,14,20,30,50):
    o=np.array([abs(C(rng.normal(0,1,n),np.ones(n))) for _ in range(N)])
    print(f"{n:>4} {np.quantile(o,.95):6.2f} {np.quantile(o,.99):6.2f} {np.quantile(o,.999):6.2f} {np.sqrt(n):11.2f}")
# 2) power: drift = mu per bar in units of sigma
n=20
print("\npower at kappa=2.58, n=20 (fraction of windows flagged coherent):")
for mu in (0.0,0.1,0.2,0.3,0.5,0.75,1.0):
    o=np.array([C(rng.normal(mu,1,n),np.ones(n)) for _ in range(60000)])
    print(f"  drift {mu:4.2f} sigma/bar -> P(C>2.58)={np.mean(o>2.58):.3f}   mean C={o.mean():5.2f}")
# 3) geometry consistency: at ignition, is target distance == observed window displacement?
n=20; d=rng.normal(0.3,1,n); m=np.ones(n)
c=C(d,m); W=m.sum(); w=m/W; neff=1/(w**2).sum(); u=np.sqrt((w*d**2).sum()); ell=np.sqrt(neff)*u
print(f"\ngeometry: C={c:.3f}  ell(risk)={ell:.3f}  target=C*ell={c*ell:.3f}  observed D=sum(delta)={d.sum():.3f}")
print(f"  R:R == C ? {np.isclose((c*ell)/ell, c)}   breakeven winrate = 1/(1+C) = {1/(1+abs(c)):.3f}")
