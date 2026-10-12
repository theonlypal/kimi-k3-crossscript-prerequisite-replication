# Frozen analysis plan

Primary endpoint: NSTOP = V0 + V2; report subtypes separately.
Pilot: five per cell, descriptive only. Confirmatory: 200 per cell, never pooled
with pilot. All recorded slots remain in denominators. Missing/error slots,
budget stops and integrity failures prevent confirmation. Exact targets and
all mixed-script strings are secondary descriptive outcomes.

Rule removal: I = pB - pA + pC - pD. Support requires complete verified data,
I > 0 and a positive Firth interaction whose profile 95% lower bound exceeds zero.
Reassignment: I = pF + pG - pE - pH. Support requires complete verified data,
positive I, both directional contrasts positive with their individual conservative
95% lower bounds above zero, both two-sided Fisher tests Holm-adjusted across
those two tests below .05, and a negative Firth interaction with profile 95%
upper bound below zero and two-sided penalized likelihood-ratio p < .05.

Numerical source plans and implementations are preserved in sources/.
Their V0-labeled binary inputs must be populated with NSTOP counts and reported
as NSTOP. Wilson 95% intervals are reported for every cell/class. Two-contrast
intervals use Bonferroni-Wilson cells within each contrast, not joint coverage
across both contrasts. Four-cell interaction intervals use four simultaneous
Bonferroni-Wilson intervals, nominal 95%. No omnibus multiplicity-adjusted claim.
Numerical failure is INCONCLUSIVE, never replaced by another analysis.
Complete intact data failing support criteria are NOT SUPPORTED, not proof of
absence. Safety/refusal/tool outcomes are non-NSTOP, not operational errors.

Reasoning text, reasoning tokens and answer bytes are separate measurements.
No post-hoc reasoning-language match enters the primary outcome. No trimming,
Unicode normalization, prompt optimization or outcome-dependent rescheduling.
If funds stop the randomized schedule early, report every remaining slot as
unrun. No confirmation from partial denominators and no pooling across models.
