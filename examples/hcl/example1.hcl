program example1
begin
	var n : int;
	n ← 678;
	do even(n) → n ← n div 2
	 □ ¬even(n) ∧ n > 1 → n ← 3 * n + 1
	od;
	print n
end
