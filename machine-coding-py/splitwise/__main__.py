
from services.splitwise_service import SplitwiseService
from strategies.split.equal_split_strategy import EqualSplitStrategy
from strategies.split.exact_split_strategy import ExactSplitStrategy
from strategies.simplify.two_pointer_simplify_strategy import TwoPointerSimplifyStrategy

service = SplitwiseService(TwoPointerSimplifyStrategy())

# --- users (each auto-joins the global group) ------------------------------
service.register_user("u1", "Akash")
service.register_user("u2", "John")
service.register_user("u3", "Mary")
service.register_user("u4", "Lee")

# --- ad-hoc 2-person expense — no group needed -----------------------------
service.add_expense(
    payer_id="u1",
    amount=50,
    participants=["u1", "u4"],
    split_strategy=EqualSplitStrategy(),
)
print("global settlements (after ad-hoc):")
for s in service.simplify_debts():
    print(" ", s)

# --- named group: equal split ---------------------------------------------
service.create_group("goa", "Trip to Goa", ["u1", "u2", "u3"])
service.add_expense(
    group_id="goa",
    payer_id="u1",
    amount=300,
    participants=["u1", "u2", "u3"],
    split_strategy=EqualSplitStrategy(),
)
print("goa settlements:")
for s in service.simplify_debts("goa"):
    print(" ", s)

# --- named group: exact split ---------------------------------------------
service.create_group("roommates", "Roommates", ["u1", "u4"])
service.add_expense(
    group_id="roommates",
    payer_id="u4",
    amount=120,
    participants=["u1", "u4"],
    split_strategy=ExactSplitStrategy(),
    shares={"u1": 70, "u4": 50},
)
print("roommates settlements:")
for s in service.simplify_debts("roommates"):
    print(" ", s)

# global stays independent from named groups
print("global settlements (unchanged by named groups):")
for s in service.simplify_debts():
    print(" ", s)

# --- validation demo: each call below should raise -------------------------
print()
bad_calls = [
    dict(group_id="ghost",     payer_id="u1",    amount=10, participants=["u1"]),
    dict(group_id="goa",       payer_id="u4",    amount=10, participants=["u1","u4"]),  # u4 not in goa
    dict(group_id="roommates", payer_id="u1",    amount=10, participants=["u1","u2"]),  # u2 not in roommates
    dict(                      payer_id="ghost", amount=10, participants=["u1"]),       # default group, unknown payer
    dict(                      payer_id="u1",    amount=-5, participants=["u1","u2"]),
]
for bad in bad_calls:
    try:
        service.add_expense(split_strategy=EqualSplitStrategy(), **bad)
    except ValueError as ex:
        print(f"[rejected] {bad} -> {ex}")


# --- DCL stress test --------------------------------------------------------
# Many threads race to create the SAME 5 users + 3 groups. With proper
# double-checked locking, exactly 5 user objects and 3 group objects exist.
print()
import threading

stress = SplitwiseService(TwoPointerSimplifyStrategy())
NUM_THREADS = 32
REPS_PER_THREAD = 200
UNIQUE_USERS = 5
UNIQUE_GROUPS = 3
ALL_USER_IDS = [f"s{i}" for i in range(UNIQUE_USERS)]

# Pre-register users in the main thread so create_group's membership check
# is always satisfied. The DCL stress is on get-or-create idempotency, not
# on the validator's pre-existence rule.
for uid in ALL_USER_IDS:
    stress.register_user(uid, f"name-{uid}")

created_users:  list[object] = []
created_groups: list[object] = []
collect_lock = threading.Lock()

def hammer(seed: int) -> None:
    local_u = []
    local_g = []
    for i in range(REPS_PER_THREAD):
        uid = ALL_USER_IDS[i % UNIQUE_USERS]
        local_u.append(stress.register_user(uid, f"name-{uid}"))   # idempotent
        gid = f"g{i % UNIQUE_GROUPS}"
        local_g.append(stress.create_group(gid, f"group-{gid}", ALL_USER_IDS))
    with collect_lock:
        created_users.extend(local_u)
        created_groups.extend(local_g)

threads = [threading.Thread(target=hammer, args=(i,)) for i in range(NUM_THREADS)]
for t in threads: t.start()
for t in threads: t.join()

unique_user_objs  = {id(u) for u in created_users}
unique_group_objs = {id(g) for g in created_groups}

print(f"DCL stress test: {NUM_THREADS} threads × {REPS_PER_THREAD} reps")
print(f"  unique user identities:  {len(unique_user_objs):>3}  (expected {UNIQUE_USERS})")
print(f"  unique group identities: {len(unique_group_objs):>3}  (expected {UNIQUE_GROUPS})")
print(f"  repo user count:         {len(stress.users):>3}")
print(f"  repo group count:        {len(stress.groups):>3}  (incl. __global__)")
assert len(unique_user_objs)  == UNIQUE_USERS,  "DCL failed: duplicate User objects"
assert len(unique_group_objs) == UNIQUE_GROUPS, "DCL failed: duplicate Group objects"
print("  OK")
