#ifndef MPI_STUB_H
#define MPI_STUB_H
#include <cstdlib>
#include <cstring>
#include <chrono>
typedef int MPI_Comm; typedef int MPI_Datatype; typedef int MPI_Op; typedef int MPI_Request; typedef int MPI_Status;
#define MPI_COMM_WORLD 0
#define MPI_INT 1
#define MPI_UINT64_T 2
#define MPI_DOUBLE 3
#define MPI_BYTE 4
#define MPI_SUM 1
#define MPI_MAX 2
#define MPI_MIN 3
#define MPI_STATUS_IGNORE ((MPI_Status*)0)
static inline int mpi_size(MPI_Datatype t){return t==MPI_INT?sizeof(int):t==MPI_UINT64_T?sizeof(unsigned long long):t==MPI_DOUBLE?sizeof(double):1;}
static inline int MPI_Init(int*,char***){return 0;} static inline int MPI_Finalize(){return 0;}
static inline int MPI_Comm_rank(MPI_Comm,int*r){*r=0;return 0;} static inline int MPI_Comm_size(MPI_Comm,int*s){*s=1;return 0;}
static inline double MPI_Wtime(){using C=std::chrono::steady_clock;return std::chrono::duration<double>(C::now().time_since_epoch()).count();}
static inline int MPI_Barrier(MPI_Comm){return 0;}
static inline int MPI_Allreduce(const void*s,void*r,int n,MPI_Datatype t,MPI_Op,MPI_Comm){std::memcpy(r,s,n*mpi_size(t));return 0;}
static inline int MPI_Allgather(const void*s,int n,MPI_Datatype t,void*r,int,MPI_Datatype,MPI_Comm){std::memcpy(r,s,n*mpi_size(t));return 0;}
static inline int MPI_Allgatherv(const void*s,int n,MPI_Datatype t,void*r,const int*,const int*d,MPI_Datatype,MPI_Comm){std::memcpy((char*)r+d[0]*mpi_size(t),s,n*mpi_size(t));return 0;}
static inline int MPI_Gather(const void*s,int n,MPI_Datatype t,void*r,int,MPI_Datatype,int,MPI_Comm){std::memcpy(r,s,n*mpi_size(t));return 0;}
static inline int MPI_Gatherv(const void*s,int n,MPI_Datatype t,void*r,const int*,const int*d,MPI_Datatype,int,MPI_Comm){std::memcpy((char*)r+d[0]*mpi_size(t),s,n*mpi_size(t));return 0;}
static inline int MPI_Bcast(void*,int,MPI_Datatype,int,MPI_Comm){return 0;}
static inline int MPI_Alltoall(const void*s,int n,MPI_Datatype t,void*r,int,MPI_Datatype,MPI_Comm){std::memcpy(r,s,n*mpi_size(t));return 0;}
static inline int MPI_Alltoallv(const void*s,const int*sc,const int*sd,MPI_Datatype,void*r,const int*,const int*rd,MPI_Datatype,MPI_Comm){if(sc[0])std::memcpy((char*)r+rd[0],(const char*)s+sd[0],sc[0]);return 0;}
static inline int MPI_Ialltoallv(const void*s,const int*sc,const int*sd,MPI_Datatype st,void*r,const int*rc,const int*rd,MPI_Datatype rt,MPI_Comm,MPI_Request*q){MPI_Alltoallv(s,sc,sd,st,r,rc,rd,rt,MPI_COMM_WORLD);*q=0;return 0;}
static inline int MPI_Wait(MPI_Request*,MPI_Status*){return 0;}
static inline int MPI_Abort(MPI_Comm,int c){std::exit(c);return c;}
#endif
