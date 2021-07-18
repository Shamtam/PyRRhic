Live Tuning Flow Chart

- Connect to ECU, check for support. If supported, create `LiveTune` instance and link with UI/backend elements. Initially only allows pulling state from ECU

State Pull:
    1. Clear state from `LiveTune` instance
    2. Pull number of dynamic tables
        If no tables, state should be INITIALIZED
        If tables, state should be COUNT
    3. If not INITIALIZED, pull headers, state should be COUNT | HEADERS
    4. If not INITIALIZED, pull tables, state should be INITIALIZED after this

State Push:
    1. If PEND_ALLOCATE:
        a. Push zeroing out of dynamic tables (set count/offset to zero)
        b. Push ROM/RAM headers and all table data (all deactivated)
        c. Push number of tables and ROM/RAM header offset
        d. Push activation of any currently activated tables
        e. Clear pending allocations, move to next write

    2. If ~TABLES:
        a. Push deactivation of all modified allocated tables
        b. Push modified table data (verification should set TABLES)
        c. Push activation of active modified allocated tables
        d. Move to next write

    3. If PEND_ACTIVATION:
        a. Push pending activations
        b. Clear pending activations
