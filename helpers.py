import hashlib

def hashword(password):
	h = hashlib.md5(password.encode())
	return h.hexdigest()



if __name__ == "__main__":
	main()