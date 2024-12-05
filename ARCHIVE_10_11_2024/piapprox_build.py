from cffi import FFI
ffibuilder = FFI()

ffibuilder.cdef("""
	float pi_approx(int n);
	""")
	
ffibuilder.set_source("_pi_cffi",
	"""
		#include "/home/traingroup/Documents/Train Group/test.h" // the C header of the library
	""")

if __name__ == "__main__":
	ffibuilder.compile(verbose=True)
