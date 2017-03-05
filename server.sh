#!/bin/bash
set -e

python -c "from mobius import Tasking; t = Tasking(); t.server()"
exit 1
