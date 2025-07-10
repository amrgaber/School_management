import xmlrpc.client

# Odoo server details
url = "http://localhost:8018"  # Change if your Odoo runs elsewhere
db = "bi_school_mgm"
username = "admin"  # Change to your Odoo username
password = "admin"  # Change to your Odoo password

# XML-RPC endpoints
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})

if not uid:
    raise Exception("Authentication failed")

models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

# Find a student record (get any student for testing)
class_ids = models.execute_kw(
    db,
    uid,
    password,
    "education.class",
    "search",
    [[]],  # Empty domain = all students
    {"limit": 1},
)

if not class_ids:
    print("No students found.")
else:
    student_id = class_ids[0]
    # Call the get_students method on the found student
    result = models.execute_kw(
        db,
        uid,
        password,
        "education.class",
        "get_student_statistics",
        [[student_id]],  # Pass as a list of IDs
    )
    print("Result of get_students:", result)
