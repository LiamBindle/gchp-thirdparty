#!/usr/bin/env/python
#
# Jinja2 is required:
# http://jinja.pocoo.org/docs/2.10/intro/#installation
#
# See README in this directory.
#

from jinja2 import Environment

template_wrappers_mpi_h = """
/**
 *  wrappers_mpi.h
 *
 *  !! DO NOT EDIT !!
 *  This file was generated by gen_wrappers_mpi.py.
 *  !! DO NOT EDIT !!
 *
 *  Wrappers for MPI calls so we can trace them.
 *  These are linked statically into the executable using
 *  --wrap=SYMBOL flags to the linker.
 *
 */

#ifndef _WRAPPERS_MPI_H
#define _WRAPPERS_MPI_H

#ifndef ESMF_MPIUNI

#include <mpi.h>

#ifdef MPICH2_CONST
#define ESMF_MPI_CONST MPICH2_CONST
#elif defined(OPEN_MPI) && OMPI_MAJOR_VERSION == 1 && OMPI_MINOR_VERSION == 7 && OMPI_RELEASE_VERSION <= 4 
#define ESMF_MPI_CONST
#elif defined(OPEN_MPI) && OMPI_MAJOR_VERSION == 1 && OMPI_MINOR_VERSION <= 6
#define ESMF_MPI_CONST 
#else
#define ESMF_MPI_CONST const
#endif

extern "C" {
  {% for f in cfunc_list %}
  {{f.ret}} __wrap_{{f.name}}({{f.params}});
  {% endfor %}

  {% for f in ffunc_list %}
  void FTN_X(__wrap_{{f.name}})({{f.params}});
  {% endfor %}
}

#endif
#endif
"""


template_wrappers_mpi = """
/**
 *  wrappers_mpi.C
 *
 *  !! DO NOT EDIT !!
 *  This file was generated by gen_wrappers_mpi.py.
 *  !! DO NOT EDIT !!
 *
 *  Wrappers for MPI calls so we can trace them.
 *  These are linked statically into the executable using
 *  --wrap=SYMBOL flags to the linker.
 *
 */

#ifndef ESMF_MPIUNI
#include <mpi.h>

#include "ESMCI_Macros.h"
#include "ESMCI_Trace.h"
#include "preload.h"
#include "wrappers_mpi.h"

extern "C" {

  static int insideMPIRegion = 0;
  static int ignorerc = 0;
  
  /*
   * C MPI functions
   */

  {% for f in cfunc_list %}
    extern {{f.ret}} __real_{{f.name}}({{f.params}});    

    {{f.ret}} __wrap_{{f.name}}({{f.params}}) {
      if (c_esmftrace_isinitialized() == 1 && insideMPIRegion == 0) {
        //printf("__wrap_{{f.name}} (C)\\n");
        insideMPIRegion = 1;
        ESMCI::TraceEventRegionEnter("{{f.name}}", &ignorerc);
        {{f.ret}} ret = __real_{{f.name}}({{f.args}});
        ESMCI::TraceEventRegionExit("{{f.name}}", &ignorerc);
        insideMPIRegion = 0;
        return ret;
      }
      else {
        return __real_{{f.name}}({{f.args}});
      }
    }
  {% endfor %}

  /*
   * Fortran MPI functions
   */

  {% for f in ffunc_list %}
    extern void FTN_X(__real_{{f.name}})({{f.params}});    

    void FTN_X(__wrap_{{f.name}})({{f.params}}) {
      if (c_esmftrace_isinitialized() == 1 && insideMPIRegion == 0) {
        //printf("__wrap_{{f.name}}_ (Fortran)\\n");
        insideMPIRegion = 1;
        ESMCI::TraceEventRegionEnter("{{f.name}}", &ignorerc);
        FTN_X(__real_{{f.name}})({{f.args}});
        ESMCI::TraceEventRegionExit("{{f.name}}", &ignorerc);
        insideMPIRegion = 0;
      }
      else {
        FTN_X(__real_{{f.name}})({{f.args}});
      }
    }
  {% endfor %}

}
#endif
"""

template_preload_mpi = """
/**
 *
 * preload_mpi.C
 *
 *  !! DO NOT EDIT !!
 *  This file was generated by gen_wrappers_mpi.py.
 *  !! DO NOT EDIT !!
 *
 * Functions that will be preloaded with LD_PRELOAD, thereby
 * overriding system library functions so we can call into our
 * wrapper function.
 *
 * Since we are using dynamic linking, the __real_<SYMBOL>
 * functions are looked up at runtime using dlsym().
 */

#ifndef ESMF_MPIUNI

#ifdef ESMF_PGIVERSION_MAJOR
/* required for RTLD_NEXT */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#endif

#include <dlfcn.h>
#include <mpi.h>

#include "ESMCI_Macros.h"
#include "ESMCI_Trace.h"
#include "wrappers_mpi.h"

#define xstr(s) str(s)
#define str(s) #s

extern "C" {

  /*
   * C MPI functions
   */

  {% for f in cfunc_list %}
    static {{f.ret}} (*__real_ptr_{{f.name}})({{f.params}}) = NULL;

    {{f.ret}} __real_{{f.name}}({{f.params}}) {
      if (__real_ptr_{{f.name}} == NULL) {
        __real_ptr_{{f.name}} = ({{f.ret}} (*)({{f.params}})) dlsym(RTLD_NEXT, "{{f.name}}");
      }
      return __real_ptr_{{f.name}}({{f.args}});
    }

    {{f.ret}} {{f.name}}({{f.params}}) {
      return __wrap_{{f.name}}({{f.args}});
    }

  {% endfor %}

  /*
   * Fortran MPI functions
   */

  {% for f in ffunc_list %}
    static void (*FTN_X(__real_ptr_{{f.name}}))({{f.params}}) = NULL;

    void FTN_X(__real_{{f.name}})({{f.params}}) {
      if (FTN_X(__real_ptr_{{f.name}}) == NULL) {
        FTN_X(__real_ptr_{{f.name}}) = (void (*)({{f.params}})) dlsym(RTLD_NEXT, xstr(FTN_X({{f.name}})));
      }
      FTN_X(__real_ptr_{{f.name}})({{f.args}});
    }

    void FTN_X({{f.name}})({{f.params}}) {
      FTN_X(__wrap_{{f.name}})({{f.args}});
    }

  {% endfor %}

}

#endif

"""

template_static_linkopts="""
ESMF_TRACE_WRAPPERS_MPI :={% for f in cfunc_list %} {{f.name}}{% if loop.index % 4 == 0 %}\nESMF_TRACE_WRAPPERS_MPI +={% endif %}{% endfor %}
ESMF_TRACE_WRAPPERS_MPI +={% for f in ffunc_list %} {{f.name}}_ {{f.name}}__{% if loop.index % 2 == 0 %}\nESMF_TRACE_WRAPPERS_MPI +={% endif %}{% endfor %}
"""


# C MPI Functions
cfunc_list = [

    {
        'ret':'int', 'name':'MPI_Allgather',
        'params':'ESMF_MPI_CONST void *sendbuf, int  sendcount, MPI_Datatype sendtype, void *recvbuf, int recvcount, MPI_Datatype recvtype, MPI_Comm comm',
        'args':'sendbuf, sendcount, sendtype, recvbuf, recvcount, recvtype, comm'
    },

    {
        'ret':'int', 'name':'MPI_Allgatherv',
        'params':'ESMF_MPI_CONST void *sendbuf, int sendcount, MPI_Datatype sendtype, void *recvbuf, ESMF_MPI_CONST int recvcounts[], ESMF_MPI_CONST int displs[], MPI_Datatype recvtype, MPI_Comm comm',
        'args':'sendbuf, sendcount, sendtype, recvbuf, recvcounts, displs, recvtype, comm'
    },

    
    {
        'ret':'int', 'name':'MPI_Allreduce',
        'params':'ESMF_MPI_CONST void *sendbuf, void *recvbuf, int count, MPI_Datatype datatype, MPI_Op op, MPI_Comm comm',
        'args':'sendbuf, recvbuf, count, datatype, op, comm'
    },

    {
        'ret':'int', 'name':'MPI_Alltoall',
        'params':'ESMF_MPI_CONST void *sendbuf, int sendcount, MPI_Datatype sendtype, void *recvbuf, int recvcount, MPI_Datatype recvtype, MPI_Comm comm',
        'args':'sendbuf, sendcount, sendtype, recvbuf, recvcount, recvtype, comm'
    },

    {
        'ret':'int', 'name':'MPI_Alltoallv',
        'params':'ESMF_MPI_CONST void *sendbuf, ESMF_MPI_CONST int sendcounts[], ESMF_MPI_CONST int sdispls[], MPI_Datatype sendtype, void *recvbuf, ESMF_MPI_CONST int recvcounts[], ESMF_MPI_CONST int rdispls[], MPI_Datatype recvtype, MPI_Comm comm',
        'args':'sendbuf, sendcounts, sdispls, sendtype, recvbuf, recvcounts, rdispls, recvtype, comm'
    },

    {
        'ret':'int', 'name':'MPI_Alltoallw',
        'params':'ESMF_MPI_CONST void *sendbuf, ESMF_MPI_CONST int sendcounts[], ESMF_MPI_CONST int sdispls[], ESMF_MPI_CONST MPI_Datatype sendtypes[], void *recvbuf, ESMF_MPI_CONST int recvcounts[], ESMF_MPI_CONST int rdispls[], ESMF_MPI_CONST MPI_Datatype recvtypes[], MPI_Comm comm',
        'args':'sendbuf, sendcounts, sdispls, sendtypes, recvbuf, recvcounts, rdispls, recvtypes, comm'
    },
    
    {
        'ret':'int', 'name':'MPI_Barrier',
        'params':'MPI_Comm comm',
        'args':'comm'
    },

    {
        'ret':'int', 'name':'MPI_Bcast',
        'params':'void *buffer, int count, MPI_Datatype datatype, int root, MPI_Comm comm',
        'args':'buffer, count, datatype, root, comm'
    },
    
    {
        'ret':'int', 'name':'MPI_Gather',
        'params':'ESMF_MPI_CONST void *sendbuf, int sendcount, MPI_Datatype sendtype, void *recvbuf, int recvcount, MPI_Datatype recvtype, int root, MPI_Comm comm',
        'args':'sendbuf, sendcount, sendtype, recvbuf, recvcount, recvtype, root, comm'
    },

    {
        'ret':'int', 'name':'MPI_Gatherv',
        'params':'ESMF_MPI_CONST void *sendbuf, int sendcount, MPI_Datatype sendtype, void *recvbuf, ESMF_MPI_CONST int recvcounts[], ESMF_MPI_CONST int displs[], MPI_Datatype recvtype, int root, MPI_Comm comm',
        'args':'sendbuf, sendcount, sendtype, recvbuf, recvcounts, displs, recvtype, root, comm'
    },

    {
        'ret':'int', 'name':'MPI_Recv',
        'params':'void *buf, int count, MPI_Datatype datatype, int source, int tag, MPI_Comm comm, MPI_Status *status',
        'args':'buf, count, datatype, source, tag, comm, status'
    },

    {
        'ret':'int', 'name':'MPI_Reduce',
        'params':'ESMF_MPI_CONST void *sendbuf, void *recvbuf, int count, MPI_Datatype datatype, MPI_Op op, int root, MPI_Comm comm',
        'args':'sendbuf, recvbuf, count, datatype, op, root, comm'
    },

    {
        'ret':'int', 'name':'MPI_Scatter',
        'params':'ESMF_MPI_CONST void *sendbuf, int sendcount, MPI_Datatype sendtype, void *recvbuf, int recvcount, MPI_Datatype recvtype, int root, MPI_Comm comm',
        'args':'sendbuf, sendcount, sendtype, recvbuf, recvcount, recvtype, root, comm'
    },
    
    {
        'ret':'int', 'name':'MPI_Send',
        'params':'ESMF_MPI_CONST void *buf, int count, MPI_Datatype datatype, int dest, int tag, MPI_Comm comm',
        'args':'buf, count, datatype, dest, tag, comm'
    },
    
    {
        'ret':'int', 'name':'MPI_Sendrecv',
        'params':'ESMF_MPI_CONST void *sendbuf, int sendcount, MPI_Datatype sendtype, int dest, int sendtag, void *recvbuf, int recvcount, MPI_Datatype recvtype, int source, int recvtag, MPI_Comm comm, MPI_Status *status',
        'args':'sendbuf, sendcount, sendtype, dest, sendtag, recvbuf, recvcount, recvtype, source, recvtag, comm, status'
    },
    
    {
        'ret':'int', 'name':'MPI_Wait',
        'params':'MPI_Request *request, MPI_Status *status',
        'args':'request, status'
    },

    {
        'ret':'int', 'name':'MPI_Waitall',
        'params':'int count, MPI_Request array_of_requests[], MPI_Status *array_of_statuses',
        'args':'count, array_of_requests, array_of_statuses'
    },

    {
        'ret':'int', 'name':'MPI_Waitany',
        'params':'int count, MPI_Request array_of_requests[], int *index, MPI_Status *status',
        'args':'count, array_of_requests, index, status'
    },

    {
        'ret':'int', 'name':'MPI_Waitsome',
        'params':'int incount, MPI_Request array_of_requests[], int *outcount, int array_of_indices[], MPI_Status array_of_statuses[]',
        'args':'incount, array_of_requests, outcount, array_of_indices, array_of_statuses'
    }
    
]


# Fortran MPI Functions
ffunc_list = [

    {
        'name':'mpi_allgather',
        'params':'MPI_Fint *sendbuf, MPI_Fint *sendcount, MPI_Fint *sendtype, MPI_Fint *recvbuf, MPI_Fint *recvcount, MPI_Fint *recvtype, MPI_Fint *comm, MPI_Fint *ierr',
        'args':'sendbuf, sendcount, sendtype, recvbuf, recvcount, recvtype, comm, ierr'
    },

    {
        'name':'mpi_allgatherv',
        'params':'MPI_Fint *sendbuf, MPI_Fint *sendcount, MPI_Fint *sendtype, MPI_Fint *recvbuf, MPI_Fint *recvcount, MPI_Fint *displs, MPI_Fint *recvtype, MPI_Fint *comm, MPI_Fint *ierr',
        'args':'sendbuf, sendcount, sendtype, recvbuf, recvcount, displs, recvtype, comm, ierr'
    },

    {
        'name':'mpi_allreduce',
        'params':'MPI_Fint *sendbuf, MPI_Fint *recvbuf, MPI_Fint *count, MPI_Fint *datatype, MPI_Fint *op, MPI_Fint *comm, MPI_Fint *ierr',
        'args':'sendbuf, recvbuf, count, datatype, op, comm, ierr'
    },

    {
        'name':'mpi_alltoall',
        'params':'MPI_Fint *sendbuf, MPI_Fint *sendcount, MPI_Fint *sendtype, MPI_Fint *recvbuf, MPI_Fint *recvcount, MPI_Fint *recvtype, MPI_Fint *comm, MPI_Fint *ierr',
        'args':'sendbuf, sendcount, sendtype, recvbuf, recvcount, recvtype, comm, ierr'
    },

    {
        'name':'mpi_alltoallv',
        'params':'MPI_Fint *sendbuf, MPI_Fint *sendcounts, MPI_Fint *sdispls, MPI_Fint *sendtype, MPI_Fint *recvbuf, MPI_Fint *recvcounts, MPI_Fint *rdispls, MPI_Fint *recvtype, MPI_Fint *comm, MPI_Fint *ierr',
        'args':'sendbuf, sendcounts, sdispls, sendtype, recvbuf, recvcounts, rdispls, recvtype, comm, ierr'
    },

    {
        'name':'mpi_alltoallw',
        'params':'MPI_Fint *sendbuf, MPI_Fint *sendcounts, MPI_Fint *sdispls, MPI_Fint *sendtypes, MPI_Fint *recvbuf, MPI_Fint *recvcounts, MPI_Fint *rdispls, MPI_Fint *recvtypes, MPI_Fint *comm, MPI_Fint *ierr',
        'args':'sendbuf, sendcounts, sdispls, sendtypes, recvbuf, recvcounts, rdispls, recvtypes, comm, ierr'
    },
    
    {
        'name':'mpi_barrier', 'params':'MPI_Fint *comm, MPI_Fint *ierr', 'args':'comm, ierr'
    },

    {
        'name':'mpi_bcast',
        'params':'MPI_Fint *buffer, MPI_Fint *count, MPI_Fint *datatype, MPI_Fint *root, MPI_Fint *comm, MPI_Fint *ierr',
        'args':'buffer, count, datatype, root, comm, ierr'
    },

    {
        'name':'mpi_exscan',
        'params':'MPI_Fint *sendbuf, MPI_Fint *recvbuf, MPI_Fint *count, MPI_Fint *datatype, MPI_Fint *op, MPI_Fint *comm, MPI_Fint *ierr',
        'args':'sendbuf, recvbuf, count, datatype, op, comm, ierr'      
    },
    
    {
        'name':'mpi_gather',
        'params':'MPI_Fint *sendbuf, MPI_Fint *sendcount, MPI_Fint *sendtype, MPI_Fint *recvbuf, MPI_Fint *recvcount, MPI_Fint *recvtype, MPI_Fint *root, MPI_Fint *comm, MPI_Fint *ierr',
        'args':'sendbuf, sendcount, sendtype, recvbuf, recvcount, recvtype, root, comm, ierr'
    },

    {
        'name':'mpi_gatherv',
        'params':'MPI_Fint *sendbuf, MPI_Fint *sendcount, MPI_Fint *sendtype, MPI_Fint *recvbuf, MPI_Fint *recvcounts, MPI_Fint *displs, MPI_Fint *recvtype, MPI_Fint *root, MPI_Fint *comm, MPI_Fint *ierr',
        'args':'sendbuf, sendcount, sendtype, recvbuf, recvcounts, displs, recvtype, root, comm, ierr'
    },

    {
        'name':'mpi_recv',
        'params':'MPI_Fint *buf, MPI_Fint *count, MPI_Fint *datatype, MPI_Fint *source, MPI_Fint *tag, MPI_Fint *comm, MPI_Fint *status, MPI_Fint *ierr',
        'args':'buf, count, datatype, source, tag, comm, status, ierr'
    },
    
    {
        'name':'mpi_reduce',
        'params':'MPI_Fint *sendbuf, MPI_Fint *recvbuf, MPI_Fint *count, MPI_Fint *datatype, MPI_Fint *op, MPI_Fint *root, MPI_Fint *comm, MPI_Fint *ierr',
        'args':'sendbuf, recvbuf, count, datatype, op, root, comm, ierr'      
    },

    {
        'name':'mpi_reduce_scatter',
        'params':'MPI_Fint *sendbuf, MPI_Fint *recvbuf, MPI_Fint *recvcounts, MPI_Fint *datatype, MPI_Fint *op, MPI_Fint *comm, MPI_Fint *ierr',
        'args':'sendbuf, recvbuf, recvcounts, datatype, op, comm, ierr'
        
    },
    
    {
        'name': 'mpi_scatter',
        'params': 'MPI_Fint *sendbuf, MPI_Fint *sendcount, MPI_Fint *sendtype, MPI_Fint *recvbuf, MPI_Fint *recvcount, MPI_Fint *recvtype, MPI_Fint *root, MPI_Fint *comm, MPI_Fint *ierr',
        'args':'sendbuf, sendcount, sendtype, recvbuf, recvcount, recvtype, root, comm, ierr'
    },

    {
        'name': 'mpi_scatterv',
        'params': 'MPI_Fint *sendbuf, MPI_Fint *sendcounts, MPI_Fint *displs, MPI_Fint *sendtype, MPI_Fint *recvbuf, MPI_Fint *recvcount, MPI_Fint *recvtype, MPI_Fint *root, MPI_Fint *comm, MPI_Fint *ierr',
        'args':'sendbuf, sendcounts, displs, sendtype, recvbuf, recvcount, recvtype, root, comm, ierr'
    },    

    {
        'name':'mpi_scan',
        'params':'MPI_Fint *sendbuf, MPI_Fint *recvbuf, MPI_Fint *count, MPI_Fint *datatype, MPI_Fint *op, MPI_Fint *comm, MPI_Fint *ierr',
        'args':'sendbuf, recvbuf, count, datatype, op, comm, ierr'      
    },

    {
        'name':'mpi_send',
        'params':'MPI_Fint *buf, MPI_Fint *count, MPI_Fint *datatype, MPI_Fint *dest, MPI_Fint *tag, MPI_Fint *comm, MPI_Fint *ierr',
        'args':'buf, count, datatype, dest, tag, comm, ierr'
    },
    
    {
        'name':'mpi_wait',
        'params':'MPI_Fint *request, MPI_Fint *status, MPI_Fint *ierr',
        'args':'request, status, ierr'
    },

    {
        'name':'mpi_waitall',
        'params':'MPI_Fint *count, MPI_Fint *reqs, MPI_Fint *stats, MPI_Fint *ierr',
        'args':'count, reqs, stats, ierr'
    },

    {
        'name':'mpi_waitany',
        'params':'MPI_Fint *count, MPI_Fint *reqs, MPI_Fint *index, MPI_Fint *status, MPI_Fint *ierr',
        'args':'count, reqs, index, status, ierr'
    }
    
]


def gen():

    template = Environment().from_string(template_wrappers_mpi_h)
    text = template.render(cfunc_list=cfunc_list, ffunc_list=ffunc_list)

    f = open('wrappers_mpi.h', 'w+')
    f.write(text)
    f.close()
    print 'Generated wrappers_mpi.h'
    
    template = Environment().from_string(template_wrappers_mpi)
    text = template.render(cfunc_list=cfunc_list, ffunc_list=ffunc_list)

    f = open('wrappers_mpi.C', 'w+')
    f.write(text)
    f.close()
    print 'Generated wrappers_mpi.C'

    template = Environment().from_string(template_preload_mpi)
    text = template.render(cfunc_list=cfunc_list, ffunc_list=ffunc_list)

    f = open('preload_mpi.C', 'w+')
    f.write(text)
    f.close()
    print 'Generated preload_mpi.C'

    template = Environment().from_string(template_static_linkopts)
    text = template.render(cfunc_list=cfunc_list, ffunc_list=ffunc_list) 
    print "\nFor use in $ESMF_DIR/build/common.mk:\n" + text
    
    
if __name__ == '__main__':
    gen()
    
