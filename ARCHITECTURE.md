# Architecture

Registration accepts 2–8 exact clause objects, normalizes IDs, sorts clauses, rejects duplicate/unknown fields, and requires positive integer weights summing to 10,000. It binds those clauses, policy, deadline, title, evidence, creator, and policy version to one fingerprint. The transaction must precede the deadline.

After the deadline, every validator independently partitions all clause IDs. The strict normalizer requires a complete disjoint partition and closed issue codes. The contract derives masks and the weighted score; creator-only first scoring is immutable.

`matches_complete_score` revalidates exact stored state and returns true only for a fingerprint-bound complete score with zero indeterminate and issue masks.
