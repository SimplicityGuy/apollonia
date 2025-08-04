## 🔄 Automated Dependency Updates

This PR contains automated dependency updates for both Python and Node.js packages.

### Update Type
**patch** updates

### What's Changed

#### Python Dependencies
- diff --git a/uv.lock b/uv.lock
- index 4662183..e90a0f8 100644
- --- a/uv.lock
- +++ b/uv.lock
- @@ -1,5 +1,5 @@
-  version = 1
- -revision = 2
- +revision = 3
-  requires-python = "==3.12.*"
-  
-  [[package]]
- @@ -366,32 +366,38 @@ wheels = [
-  
-  [[package]]
-  name = "bcrypt"
- -version = "4.2.1"
- -source = { registry = "https://pypi.org/simple" }
- -sdist = { url = "https://files.pythonhosted.org/packages/56/8c/dd696962612e4cd83c40a9e6b3db77bfe65a830f4b9af44098708584686c/bcrypt-4.2.1.tar.gz", hash = "sha256:6765386e3ab87f569b276988742039baab087b2cdb01e809d74e74503c2faafe", size = 24427, upload-time = "2024-11-19T20:08:07.159Z" }
- -wheels = [
- -    { url = "https://files.pythonhosted.org/packages/bc/ca/e17b08c523adb93d5f07a226b2bd45a7c6e96b359e31c1e99f9db58cb8c3/bcrypt-4.2.1-cp37-abi3-macosx_10_12_universal2.whl", hash = "sha256:1340411a0894b7d3ef562fb233e4b6ed58add185228650942bdc885362f32c17", size = 489982, upload-time = "2024-11-19T20:07:21.899Z" },

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
