# Starting MongoDB Server for Compass

## Option 1: Start MongoDB Server (Windows)

If you have MongoDB installed with Compass, the server should also be installed. Try these commands:

```powershell
# Try starting as a service (run PowerShell as Administrator)
net start MongoDB

# If that doesn't work, try:
"C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" --dbpath "C:\data\db"

# Or for version 6.0:
"C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe" --dbpath "C:\data\db"
```

**Note**: You may need to create the data directory first:
```powershell
mkdir C:\data\db
```

## Option 2: Find MongoDB Installation

```powershell
# Find where MongoDB is installed
where mongod

# Or search in common locations:
dir "C:\Program Files\MongoDB" /s /b
```

## Option 3: Connect to MongoDB Compass

Once the server is running:

1. **Open MongoDB Compass**
2. **Connection String**: `mongodb://localhost:27017`
3. Click **Connect**
4. You should see the connection succeed

## Option 4: Use MongoDB Atlas (Cloud - Free)

If you can't get the local server running, use MongoDB Atlas:

1. Go to https://www.mongodb.com/cloud/atlas/register
2. Create a free account and cluster
3. Get your connection string (looks like: `mongodb+srv://...`)
4. Update `backend/.env`:
   ```
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
   ```
5. Use the same connection string in Compass

## Verify MongoDB is Running

After starting MongoDB, test the connection:

```powershell
# In a new terminal
mongo
# Or if using newer versions:
mongosh
```

If this connects successfully, your backend should also connect!
