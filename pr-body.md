## 🔄 Automated Dependency Updates

This PR contains automated dependency updates for both Python and Node.js packages.

### Update Type
**patch** updates

### What's Changed

#### Python Dependencies
- diff --git a/uv.lock b/uv.lock
- index 4662183..4671394 100644
- --- a/uv.lock
- +++ b/uv.lock
- @@ -1,5 +1,5 @@
-  version = 1
- -revision = 2
- +revision = 3
-  requires-python = "==3.12.*"
-  
-  [[package]]
- @@ -13,16 +13,15 @@ wheels = [
-  
-  [[package]]
-  name = "aio-pika"
- -version = "9.5.5"
- +version = "9.5.7"
-  source = { registry = "https://pypi.org/simple" }
-  dependencies = [
-      { name = "aiormq" },

#### Node.js Dependencies


### Testing
- ✅ Python unit tests passed
- ✅ Python linting and type checking passed
- ✅ Node.js tests passed
- ✅ Node.js linting and type checking passed
- ✅ Frontend build successful

### Security
- ✅ No high-severity vulnerabilities detected

---

🤖 This PR was automatically created by the dependency update workflow.
