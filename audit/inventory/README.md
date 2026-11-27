# Inventory analysis

Scripts that read the tables of `institute inventory` (swift-institute/institute, branch `inventory`) and compute the
figures behind the rules for types, targets, products, repositories and organizations (coenttb/dotfiles#38).

    institute inventory --root <plain clones> --output <tables> --exclude rule-legal
    ./load.py <tables> inv.db      # the JSON tables into SQLite; the scripts expect it at /home/user/analysis/inv.db
    ./xy.py && ./tg.py             # every multi-word repository by the type its name matches; targets and products
    ./glue.py ; ./partial.py       # platform and Foundation use per target; targets with a dependency the primary lacks
    ./i1.py ; ./nf.py ; ./fold.py  # the letter of I1; why each target exists; which kind packages fold without a cycle

The clones must be plain: `sync.sh` rewrites manifests to path dependencies, which changes a dependency's location.
The results name private repositories and are not kept here.
