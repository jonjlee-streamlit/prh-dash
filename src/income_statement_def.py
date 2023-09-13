"""
Defines how to convert a table of raw revenue/expense items to a readable income statement
"""
INCOME_STATEMENT_DEF = [
    {
        "name": "Operating Revenues",
        "items": [
            {
                "name": "Patient Revenues",
                "items": [
                    {
                        "name": "Inpatient",
                        "items": [
                            {
                                "account": "40000:Patient Revenues",
                                "category": "Inpatient Revenue",
                                "negative": True,
                            }
                        ],
                    },
                    {
                        "name": "Outpatient",
                        "items": [
                            {
                                "account": "40000:Patient Revenues",
                                "category": "Outpatient Revenue",
                                "negative": True,
                            },
                            {
                                "account": "40000:Patient Revenues",
                                "category": "Clinic Revenue",
                                "negative": True,
                            },
                        ],
                    },
                ],
            },
            {
                "name": "Other",
                "items": [
                    {
                        "account": "40010:Sales Revenue",
                        "category": "*",
                        "negative": True,
                    },
                    {
                        "account": "40300:Other Operating Revenue",
                        "category": "*",
                        "negative": True,
                    },
                    {
                        "account": "40301:Gain/Loss on Sale",
                        "negative": True,
                    },
                ],
            },
        ],
    },
    {
        "name": "Deductions",
        "items": [
            {"account": "49000:Contractual Adjustments"},
            {"account": "49001:Bad Debts & Write Offs"},
            {"account": "49002:Administrative Write Offs"},
            {"account": "49003:Employee Discount"},
        ],
    },
    {"name": "Net Revenue", "total": ["Operating Revenues", "-Deductions"]},
    {
        "name": "Expenses",
        "items": [
            {
                "name": "Salaries",
                "items": [{"account": "50000:Salaries & Wages", "category": "*"}],
            },
            {
                "name": "Employee Benefits",
                "items": [
                    {"account": "50011:Benefits-Taxes", "category": "*"},
                    {"account": "50012:Benefits-Insurance", "category": "*"},
                    {"account": "50013:Benefits-Retirement", "category": "*"},
                    {"account": "50014:Benefits-Other", "category": "*"},
                ],
            },
            {
                "name": "Professional Fees",
                "items": [
                    {"account": "60220:Professional Fees", "category": "*"},
                    {"account": "60221:Temp Labor", "category": "*"},
                    {"account": "60222:Locum Tenens", "category": "*"},
                ],
            },
            {
                "name": "Supplies",
                "items": [
                    {"account": "60300:Supplies", "category": "*"},
                    {"account": "60301:Inventory Adjustments", "category": "*"},
                    {"account": "60302:Expired Wasted Supplies", "category": "*"},
                    {"account": "60336:Pharmaceuticals", "category": "*"},
                ],
            },
            {
                "name": "Utilities",
                "items": [
                    {"account": "60500:Utilities", "category": "*"},
                ],
            },
            {
                "name": "Puchased Services",
                "items": [
                    {"account": "60600:Purchased Services", "category": "*"},
                    {"account": "60620:Maintenance", "category": "*"},
                    {"account": "60650:Software Licenses", "category": "*"},
                ],
            },
            {
                "name": "Depreciation",
                "items": [
                    {"account": "70000:Depreciation", "category": "*"},
                ],
            },
            {
                "name": "Rental/Leases",
                "items": [
                    {"account": "60800:Leases/Rents Operating", "category": "*"},
                ],
            },
            {
                "name": "Insurance",
                "items": [
                    {"account": "60900:Insurance-Professional", "category": "*"},
                    {"account": "60901:Insurance-Other", "category": "*"},
                ],
            },
            {
                "name": "Licenses & Taxes",
                "items": [
                    {"account": "61000:Taxes-Hospital B&O", "category": "*"},
                    {"account": "61001:Taxes-Sales and Use", "category": "*"},
                    {"account": "61002:Taxes-Property", "category": "*"},
                    {"account": "61003:Licensing Fees State", "category": "*"},
                ],
            },
            {
                "name": "Other Direct Expenses",
                "items": [
                    {"account": "60951:Professional Memberships", "category": "*"},
                    {"account": "60960:Other Direct Expenses", "category": "*"},
                    {"account": "60970:Travel & Education", "category": "*"},
                ],
            },
            {
                "name": "Interest/Amortization/Fees",
                "items": [
                    {
                        "account": "80000:Interest/Bond Amortz/Trustee Fees",
                        "category": "*",
                    },
                ],
            },
        ],
    },
    {"name": "Total Operating Expenses", "total": ["Expenses/"]},
    {
        "name": "Operating Margin",
        "total": ["Operating Revenues/", "-Deductions/", "-Expenses/"],
    },
]