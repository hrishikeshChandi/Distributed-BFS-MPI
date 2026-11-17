#include <mpi.h>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <limits>
#include <numeric>
#include <queue>
#include <sstream>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

using u64 = uint64_t;
using i64 = int64_t;
struct Edge { u64 src, dst; };
struct Pair { u64 vertex, parent; };
static_assert(sizeof(Edge)==16, "Edge wire format must be two uint64 values");
static_assert(sizeof(Pair)==16, "Pair wire format must be two uint64 values");
struct Options {
  int scale=16, edge_factor=8, repetitions=16; bool directed=false, synthetic=true;
  std::string input="", ordering="original", mode="blocking", dataset="rmat";
  u64 graph_seed=12345, permutation_seed=0xBADC0FFEE0DDF00DULL, source_seed=98765;
  std::string summary="results/summary.csv", levels="results/per_level.csv", ranks="results/rank_metrics.csv";
  u64 reference_max_vertices=1ULL<<21;
};
static u64 splitmix64(u64 x){ x+=0x9e3779b97f4a7c15ULL; x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL; x=(x^(x>>27))*0x94d049bb133111ebULL; return x^(x>>31); }
static int owner_of(u64 v,u64 n,int p){ return (int)((((__uint128_t)(v+1)*p)-1)/n); }
static u64 permute(u64 x,u64 n,u64 seed){
  // Eight-round balanced Feistel permutation with cycle-walking over [0,n).
  // Cycle-walking restricts a power-of-two-domain permutation to arbitrary N
  // without collisions, so SNAP and R-MAT IDs are both mapped bijectively.
  if(n<=1) return x;
  if(n>(1ULL<<62)) throw std::runtime_error("Random relabelling supports at most 2^62 vertices");
  unsigned bits=0;
  u64 domain=1;
  while(domain<n){ domain<<=1; ++bits; }
  if(bits&1U){ domain<<=1; ++bits; }
  const unsigned half=bits/2;
  const u64 mask=(1ULL<<half)-1ULL;
  auto permute_domain=[&](u64 value){
    u64 left=(value>>half)&mask, right=value&mask;
    for(u64 round=0;round<8;round++){
      const u64 key=splitmix64(seed + 0x9e3779b97f4a7c15ULL*(round+1));
      const u64 f=splitmix64(right ^ key)&mask;
      const u64 next_left=right;
      const u64 next_right=(left ^ f)&mask;
      left=next_left; right=next_right;
    }
    return (left<<half)|right;
  };
  u64 y=x;
  do { y=permute_domain(y); } while(y>=n);
  return y;
}
static Options parse(int argc,char**argv){ Options o; for(int i=1;i<argc;i++){std::string k=argv[i]; auto val=[&](){if(i+1>=argc) throw std::runtime_error("Missing value for "+k); return std::string(argv[++i]);};
 if(k=="--scale")o.scale=std::stoi(val()); else if(k=="--edge-factor")o.edge_factor=std::stoi(val()); else if(k=="--repetitions")o.repetitions=std::stoi(val()); else if(k=="--input"){o.input=val();o.synthetic=false;} else if(k=="--dataset")o.dataset=val(); else if(k=="--ordering")o.ordering=val(); else if(k=="--mode")o.mode=val(); else if(k=="--directed")o.directed=std::stoi(val())!=0; else if(k=="--graph-seed")o.graph_seed=std::stoull(val()); else if(k=="--permutation-seed")o.permutation_seed=std::stoull(val()); else if(k=="--source-seed")o.source_seed=std::stoull(val()); else if(k=="--summary-csv")o.summary=val(); else if(k=="--per-level-csv")o.levels=val(); else if(k=="--rank-csv")o.ranks=val(); else if(k=="--reference-max-vertices")o.reference_max_vertices=std::stoull(val()); else if(k=="--help"){std::cout<<"--scale 16..24 --edge-factor 8 --repetitions 16 --input FILE --directed 0|1 --ordering original|random --mode blocking|nonblocking --summary-csv FILE --per-level-csv FILE --rank-csv FILE\n"; std::exit(0);} else throw std::runtime_error("Unknown option: "+k); }
 if(o.scale<1||o.scale>40||o.edge_factor<1||o.repetitions<1) throw std::runtime_error("Invalid scale/edge-factor/repetitions");
 if(o.ordering!="original"&&o.ordering!="random") throw std::runtime_error("ordering must be original|random");
 if(o.mode!="blocking"&&o.mode!="nonblocking") throw std::runtime_error("mode must be blocking|nonblocking");
 return o; }
static void mkdir_parent(const std::string&f){auto p=f.find_last_of('/');if(p!=std::string::npos) {std::string cmd="mkdir -p '"+f.substr(0,p)+"'"; std::system(cmd.c_str());}}
static void append_csv(const std::string&f,const std::string&header,const std::string&line){mkdir_parent(f); bool exists=std::ifstream(f).good(); std::ofstream out(f,std::ios::app); if(!exists)out<<header<<"\n";out<<line<<"\n";}
static void build_local_csr(u64 n,int rank,int p,std::vector<Edge>&local_edges,u64 &start,std::vector<u64>&offset,std::vector<u64>&adj){
 start=(u64)(((__uint128_t)n*rank)/p);u64 end=(u64)(((__uint128_t)n*(rank+1))/p);
 std::sort(local_edges.begin(),local_edges.end(),[](const Edge&a,const Edge&b){return a.src<b.src||(a.src==b.src&&a.dst<b.dst);});
 local_edges.erase(std::unique(local_edges.begin(),local_edges.end(),[](const Edge&a,const Edge&b){return a.src==b.src&&a.dst==b.dst;}),local_edges.end());
 offset.assign((size_t)(end-start)+1,0);for(const auto&e:local_edges)if(e.src>=start&&e.src<end&&e.dst<n)offset[e.src-start+1]++;
 for(size_t i=1;i<offset.size();i++) offset[i]+=offset[i-1];
 adj.resize(offset.back());std::vector<u64> cursor=offset;
 for(const auto&e:local_edges)if(e.src>=start&&e.src<end&&e.dst<n)adj[cursor[e.src-start]++]=e.dst;
 std::vector<Edge>().swap(local_edges);
}
static void distribute_edges(std::vector<Edge>&source_edges,u64 n,int p,std::vector<Edge>&local){
 if(p==1){local=std::move(source_edges);return;}
 std::vector<int> sc(p,0),rc(p,0),sd(p,0),rd(p,0);
 for(const auto&e:source_edges) sc[owner_of(e.src,n,p)]++;
 MPI_Alltoall(sc.data(),1,MPI_INT,rc.data(),1,MPI_INT,MPI_COMM_WORLD);
 int ns=0,nr=0;for(int i=0;i<p;i++){sd[i]=ns;ns+=sc[i];rd[i]=nr;nr+=rc[i];}
 std::vector<Edge> packed(ns);auto cur=sd;for(const auto&e:source_edges)packed[cur[owner_of(e.src,n,p)]++]=e;std::vector<Edge>().swap(source_edges);
 std::vector<int> sb(p),rb(p),sdb(p),rdb(p);for(int i=0;i<p;i++){sb[i]=sc[i]*sizeof(Edge);rb[i]=rc[i]*sizeof(Edge);sdb[i]=sd[i]*sizeof(Edge);rdb[i]=rd[i]*sizeof(Edge);} local.resize(nr);
 MPI_Alltoallv(packed.data(),sb.data(),sdb.data(),MPI_BYTE,local.data(),rb.data(),rdb.data(),MPI_BYTE,MPI_COMM_WORLD);
}
static std::pair<u64,u64> rmat_edge(u64 id,int scale,u64 seed){u64 x=splitmix64(seed ^ id),a=0,b=0;for(int bit=scale-1;bit>=0;--bit){double r=(double)(splitmix64(x+(u64)bit)%1000000)/1000000.0;double A=0.57,B=0.19,C=0.19;int q=(r<A)?0:(r<A+B)?1:(r<A+B+C)?2:3;if(q==1||q==3)a|=(1ULL<<bit);if(q==2||q==3)b|=(1ULL<<bit);}return {a,b};}
static std::vector<Edge> make_rmat_edges(const Options&o,int rank,int p,u64 n){u64 m=n*(u64)o.edge_factor;u64 lo=(u64)(((__uint128_t)m*rank)/p),hi=(u64)(((__uint128_t)m*(rank+1))/p);std::vector<Edge> e;e.reserve((hi-lo)*(o.directed?1:2));for(u64 id=lo;id<hi;id++){auto ab=rmat_edge(id,o.scale,o.graph_seed);u64 a=ab.first,b=ab.second;if(a==b)continue;if(o.ordering=="random"){a=permute(a,n,o.permutation_seed);b=permute(b,n,o.permutation_seed);}e.push_back({a,b});if(!o.directed)e.push_back({b,a});}return e;}
static bool load_snap_root(const Options&o,std::vector<Edge>&edges,u64&n,int rank){if(rank!=0)return true;std::ifstream in(o.input);if(!in){std::cerr<<"Cannot open graph file: "<<o.input<<"\n";return false;}std::string line;u64 mx=0,mn=std::numeric_limits<u64>::max();std::vector<Edge> raw;while(std::getline(in,line)){if(line.empty()||line[0]=='#'||line[0]=='%'||line[0]=='\n')continue;std::istringstream ss(line);u64 a,b;if(!(ss>>a>>b))continue;raw.push_back({a,b});mn=std::min(mn,std::min(a,b));mx=std::max(mx,std::max(a,b));}if(raw.empty()){std::cerr<<"No edge pairs parsed from SNAP file\n";return false;} // SNAP IDs are remapped densely after min/max normalization; holes are retained to preserve identity.
 n=mx-mn+1;edges.reserve(raw.size()*(o.directed?1:2));for(auto&e:raw){u64 a=e.src-mn,b=e.dst-mn;if(o.ordering=="random"){a=permute(a,n,o.permutation_seed);b=permute(b,n,o.permutation_seed);}edges.push_back({a,b});if(!o.directed)edges.push_back({b,a});}return true;}
static void write_rank_metrics(const std::string&file,const std::string&dataset,const std::string&ordering,int rank,int p,u64 n,u64 start,const std::vector<u64>&off,const std::vector<u64>&adj){u64 local_edges=adj.size(),cut=0;for(auto v:adj)if(owner_of(v,n,p)!=rank)cut++;u64 mine[2]={local_edges,cut};std::vector<u64> all(rank==0?2*p:0);MPI_Gather(mine,2,MPI_UINT64_T,all.data(),2,MPI_UINT64_T,0,MPI_COMM_WORLD);if(rank==0)for(int r=0;r<p;r++){std::ostringstream l;l<<dataset<<","<<ordering<<","<<r<<","<<p<<","<<n<<","<<all[2*r]<<","<<all[2*r+1];append_csv(file,"dataset,ordering,rank,ranks,vertices,local_adjacency_entries,local_cut_edges",l.str());}(void)start;(void)off;}
struct LevelRow{
 int level;
 double expansion_ms,packing_ms,count_exchange_ms,collective_request_ms;
 double localcand_ms,residual_wait_ms,merge_ms,wall_ms;
 u64 frontier,remote;
 double imbalance;
};
struct LocalLevelRow{
 double expansion_ms,packing_ms,count_exchange_ms,collective_request_ms;
 double localcand_ms,residual_wait_ms,merge_ms,wall_ms;
 u64 global_frontier,local_frontier,remote;
};
static bool distributed_bfs(u64 n,u64 start,const std::vector<u64>&off,const std::vector<u64>&adj,u64 root,int rank,int p,bool nonblocking,std::vector<int>&local_levels,std::vector<u64>&local_parent,std::vector<LevelRow>&rows,double&elapsed,u64&scanned,u64&remote_total){
 u64 end=start+off.size()-1;
 local_levels.assign(end-start,-1);
 local_parent.assign(end-start,std::numeric_limits<u64>::max());
 std::vector<u64> frontier;
 if(root>=start&&root<end){local_levels[root-start]=0;local_parent[root-start]=root;frontier.push_back(root);}
 MPI_Barrier(MPI_COMM_WORLD);
 const double t0=MPI_Wtime();
 int level=0;
 scanned=0; remote_total=0;
 std::vector<LocalLevelRow> local_rows;
 while(true){
  const double level0=MPI_Wtime();
  std::vector<std::vector<Pair>> send(p);
  std::vector<Pair> localcand;
  std::vector<u64> next;
  u64 local_scanned=0;
  const double expansion0=MPI_Wtime();
  for(u64 u:frontier){
   const u64 ix=u-start;
   for(u64 j=off[ix];j<off[ix+1];j++){
    const u64 v=adj[j]; local_scanned++;
    if(v>=start&&v<end){if(local_levels[v-start]<0)localcand.push_back({v,u});}
    else send[owner_of(v,n,p)].push_back({v,u});
   }
  }
  const double expansion_ms=(MPI_Wtime()-expansion0)*1000.0;
  scanned+=local_scanned;

  // Separate CPU preparation/packing from the count collective itself.
  const double preparation0=MPI_Wtime();
  std::vector<int> sc(p),rc(p),sd(p),rd(p);
  for(int q=0;q<p;q++)sc[q]=(int)send[q].size();
  const double count0=MPI_Wtime();
  MPI_Alltoall(sc.data(),1,MPI_INT,rc.data(),1,MPI_INT,MPI_COMM_WORLD);
  const double count_exchange_ms=(MPI_Wtime()-count0)*1000.0;
  int ns=0,nr=0;
  for(int q=0;q<p;q++){sd[q]=ns;ns+=sc[q];rd[q]=nr;nr+=rc[q];}
  std::vector<Pair> sbuf(ns),rbuf(nr);
  for(int q=0;q<p;q++)std::copy(send[q].begin(),send[q].end(),sbuf.begin()+sd[q]);
  std::vector<int> sbyte(p),rbyte(p),sdbyte(p),rdbyte(p);
  for(int q=0;q<p;q++){
   sbyte[q]=sc[q]*(int)sizeof(Pair); rbyte[q]=rc[q]*(int)sizeof(Pair);
   sdbyte[q]=sd[q]*(int)sizeof(Pair); rdbyte[q]=rd[q]*(int)sizeof(Pair);
  }
  const double packing_ms=std::max(0.0,(MPI_Wtime()-preparation0)*1000.0-count_exchange_ms);

  double localcand_ms=0.0,residual_wait_ms=0.0;
  double collective_request_ms=0.0;
  if(nonblocking){
   const double request0=MPI_Wtime();
   MPI_Request req;
   MPI_Ialltoallv(sbuf.data(),sbyte.data(),sdbyte.data(),MPI_BYTE,
                  rbuf.data(),rbyte.data(),rdbyte.data(),MPI_BYTE,MPI_COMM_WORLD,&req);
   const double local0=MPI_Wtime();
   for(const auto&x:localcand){
    if(local_levels[x.vertex-start]<0){
     local_levels[x.vertex-start]=level+1; local_parent[x.vertex-start]=x.parent;
     next.push_back(x.vertex);
    }
   }
   localcand_ms=(MPI_Wtime()-local0)*1000.0;
   const double wait0=MPI_Wtime();
   MPI_Wait(&req,MPI_STATUS_IGNORE);
   residual_wait_ms=(MPI_Wtime()-wait0)*1000.0;
   collective_request_ms=(MPI_Wtime()-request0)*1000.0; // includes overlapped local work
  }else{
   const double request0=MPI_Wtime();
   MPI_Alltoallv(sbuf.data(),sbyte.data(),sdbyte.data(),MPI_BYTE,
                 rbuf.data(),rbyte.data(),rdbyte.data(),MPI_BYTE,MPI_COMM_WORLD);
   collective_request_ms=(MPI_Wtime()-request0)*1000.0;
   const double local0=MPI_Wtime();
   for(const auto&x:localcand){
    if(local_levels[x.vertex-start]<0){
     local_levels[x.vertex-start]=level+1; local_parent[x.vertex-start]=x.parent;
     next.push_back(x.vertex);
    }
   }
   localcand_ms=(MPI_Wtime()-local0)*1000.0;
  }

  const double merge0=MPI_Wtime();
  for(const auto&x:rbuf){
   if(x.vertex>=start&&x.vertex<end&&local_levels[x.vertex-start]<0){
    local_levels[x.vertex-start]=level+1; local_parent[x.vertex-start]=x.parent;
    next.push_back(x.vertex);
   }
  }
  const double merge_ms=(MPI_Wtime()-merge0)*1000.0;
  const u64 locnext=next.size();
  u64 globnext=0;
  // This is the only per-level reduction kept in the timed loop; it is
  // required to determine global BFS termination correctly.
  MPI_Allreduce(&locnext,&globnext,1,MPI_UINT64_T,MPI_SUM,MPI_COMM_WORLD);
  const double wall_ms=(MPI_Wtime()-level0)*1000.0;
  local_rows.push_back({expansion_ms,packing_ms,count_exchange_ms,collective_request_ms,
                        localcand_ms,residual_wait_ms,merge_ms,wall_ms,globnext,locnext,(u64)ns});
  frontier.swap(next);
  level++;
  if(globnext==0)break;
 }
 // Stop the BFS timer before reducing diagnostic arrays. These post-run
 // reductions do not contribute to elapsed_ms / TEPS.
 elapsed=MPI_Wtime()-t0;
 const int levels=(int)local_rows.size();
 std::vector<double> local_times((size_t)levels*8),global_times((size_t)levels*8);
 std::vector<u64> local_remote(levels),global_remote(levels),local_frontier(levels),max_frontier(levels);
 for(int i=0;i<levels;i++){
  const auto&r=local_rows[i];
  const size_t b=(size_t)i*8;
  local_times[b+0]=r.expansion_ms; local_times[b+1]=r.packing_ms;
  local_times[b+2]=r.count_exchange_ms; local_times[b+3]=r.collective_request_ms;
  local_times[b+4]=r.localcand_ms; local_times[b+5]=r.residual_wait_ms;
  local_times[b+6]=r.merge_ms; local_times[b+7]=r.wall_ms;
  local_remote[i]=r.remote; local_frontier[i]=r.local_frontier;
 }
 MPI_Allreduce(local_times.data(),global_times.data(),levels*8,MPI_DOUBLE,MPI_MAX,MPI_COMM_WORLD);
 MPI_Allreduce(local_remote.data(),global_remote.data(),levels,MPI_UINT64_T,MPI_SUM,MPI_COMM_WORLD);
 MPI_Allreduce(local_frontier.data(),max_frontier.data(),levels,MPI_UINT64_T,MPI_MAX,MPI_COMM_WORLD);
 for(int i=0;i<levels;i++){
  const size_t b=(size_t)i*8;
  const u64 global_sum=local_rows[i].global_frontier;
  const double imbalance=global_sum?double(max_frontier[i])/(double(global_sum)/p):0.0;
  remote_total+=global_remote[i];
  if(rank==0)rows.push_back({i,global_times[b+0],global_times[b+1],global_times[b+2],global_times[b+3],
                             global_times[b+4],global_times[b+5],global_times[b+6],global_times[b+7],
                             global_sum,global_remote[i],imbalance});
 }
 return true;
}
static bool validate_parent_tree(u64 n,u64 start,const std::vector<u64>&off,const std::vector<u64>&adj,const std::vector<int>&lev,const std::vector<u64>&par,u64 root,int p){
 int localn=(int)lev.size();std::vector<int> counts(p),displs(p);MPI_Allgather(&localn,1,MPI_INT,counts.data(),1,MPI_INT,MPI_COMM_WORLD);int total=0;for(int i=0;i<p;i++){displs[i]=total;total+=counts[i];}
 std::vector<int> alllev(total);std::vector<u64> allpar(total);MPI_Allgatherv(lev.data(),localn,MPI_INT,alllev.data(),counts.data(),displs.data(),MPI_INT,MPI_COMM_WORLD);MPI_Allgatherv(par.data(),localn,MPI_UINT64_T,allpar.data(),counts.data(),displs.data(),MPI_UINT64_T,MPI_COMM_WORLD);
 int bad=0;u64 end=start+off.size()-1,local_reached=0,local_parent_edges=0;for(u64 v=start;v<end;v++){int l=lev[v-start];if(l>=0)local_reached++;if(v==root){if(l!=0||par[v-start]!=v)bad++;}else if(l>=0){u64 pr=par[v-start];if(pr>=n||alllev[pr]!=l-1)bad++;}else if(par[v-start]!=std::numeric_limits<u64>::max())bad++;}
 for(u64 u=start;u<end;u++){int lu=lev[u-start];for(u64 j=off[u-start];j<off[u-start+1];j++){u64 v=adj[j];if(lu>=0&&(alllev[v]<0||alllev[v]>lu+1))bad++;if(allpar[v]==u&&alllev[v]==lu+1)local_parent_edges++;}}
 u64 reached=0,parent_edges=0;MPI_Allreduce(&local_reached,&reached,1,MPI_UINT64_T,MPI_SUM,MPI_COMM_WORLD);MPI_Allreduce(&local_parent_edges,&parent_edges,1,MPI_UINT64_T,MPI_SUM,MPI_COMM_WORLD);if(parent_edges+1!=reached)bad++;
 int totalbad=0;MPI_Allreduce(&bad,&totalbad,1,MPI_INT,MPI_SUM,MPI_COMM_WORLD);return totalbad==0;
}
static bool sequential_reference_check(u64 n,u64 start,const std::vector<u64>&off,const std::vector<u64>&adj,const std::vector<int>&dist,u64 root,int rank,int p,u64 max_vertices){if(n>max_vertices)return true;std::vector<int> counts(p),displs(p);u64 localn=off.size()-1;int ln=(int)localn;MPI_Allgather(&ln,1,MPI_INT,counts.data(),1,MPI_INT,MPI_COMM_WORLD);int total=0;for(int i=0;i<p;i++){displs[i]=total;total+=counts[i];}std::vector<int> all(total);MPI_Gatherv(dist.data(),ln,MPI_INT,all.data(),counts.data(),displs.data(),MPI_INT,0,MPI_COMM_WORLD);std::vector<Edge> localE;for(u64 u=0;u<localn;u++)for(u64 j=off[u];j<off[u+1];j++)localE.push_back({start+u,adj[j]});int ec=localE.size();std::vector<int> ecs(p),eds(p);MPI_Gather(&ec,1,MPI_INT,ecs.data(),1,MPI_INT,0,MPI_COMM_WORLD);std::vector<Edge> allE;if(rank==0){int sum=0;for(int i=0;i<p;i++){eds[i]=sum;sum+=ecs[i];}allE.resize(sum);}std::vector<int> ecounts(p),edis(p);for(int i=0;i<p;i++){ecounts[i]=ecs[i]*(int)sizeof(Edge);edis[i]=eds[i]*(int)sizeof(Edge);}MPI_Gatherv(localE.data(),ec*(int)sizeof(Edge),MPI_BYTE,allE.data(),ecounts.data(),edis.data(),MPI_BYTE,0,MPI_COMM_WORLD);int ok=1;if(rank==0){std::vector<std::vector<u64>> g(n);for(auto&e:allE)g[e.src].push_back(e.dst);std::vector<int> ref(n,-1);std::queue<u64>q;ref[root]=0;q.push(root);while(!q.empty()){u64 u=q.front();q.pop();for(u64 v:g[u])if(ref[v]<0){ref[v]=ref[u]+1;q.push(v);}}if(ref!=all)ok=0;}MPI_Bcast(&ok,1,MPI_INT,0,MPI_COMM_WORLD);return ok==1;}
int main(int argc,char**argv){MPI_Init(&argc,&argv);int rank,p;MPI_Comm_rank(MPI_COMM_WORLD,&rank);MPI_Comm_size(MPI_COMM_WORLD,&p);try{Options o=parse(argc,argv);u64 n=o.synthetic?(1ULL<<o.scale):0;std::vector<Edge> source_edges;if(o.synthetic){source_edges=make_rmat_edges(o,rank,p,n);}else{if(!load_snap_root(o,source_edges,n,rank)){MPI_Abort(MPI_COMM_WORLD,2);}}MPI_Bcast(&n,1,MPI_UINT64_T,0,MPI_COMM_WORLD);std::vector<Edge> local_edges;distribute_edges(source_edges,n,p,local_edges);std::vector<u64> off,adj;u64 start;build_local_csr(n,rank,p,local_edges,start,off,adj);write_rank_metrics(o.ranks,o.dataset,o.ordering,rank,p,n,start,off,adj);u64 global_m=0,locm=adj.size();MPI_Allreduce(&locm,&global_m,1,MPI_UINT64_T,MPI_SUM,MPI_COMM_WORLD);std::vector<u64> sources;std::unordered_set<u64> seen_sources;u64 wanted=std::min<u64>(o.repetitions,n);for(u64 i=0;sources.size()<wanted;i++){u64 x=splitmix64(o.source_seed+i)%n;if(seen_sources.insert(x).second)sources.push_back(x);}if(o.ordering=="random")for(auto&x:sources)x=permute(x,n,o.permutation_seed);
 for(size_t rep=0;rep<sources.size();rep++){std::vector<int> lev;std::vector<u64> par;std::vector<LevelRow> rows;double elapsed=0;u64 scanned=0,remote=0;distributed_bfs(n,start,off,adj,sources[rep],rank,p,o.mode=="nonblocking",lev,par,rows,elapsed,scanned,remote);bool tree=validate_parent_tree(n,start,off,adj,lev,par,sources[rep],p);bool ref=sequential_reference_check(n,start,off,adj,lev,sources[rep],rank,p,o.reference_max_vertices);int valid=(tree&&ref)?1:0;int allvalid;MPI_Allreduce(&valid,&allvalid,1,MPI_INT,MPI_MIN,MPI_COMM_WORLD);double maxelapsed;MPI_Allreduce(&elapsed,&maxelapsed,1,MPI_DOUBLE,MPI_MAX,MPI_COMM_WORLD);u64 gscan;MPI_Allreduce(&scanned,&gscan,1,MPI_UINT64_T,MPI_SUM,MPI_COMM_WORLD);u64 reach=0;for(int x:lev)if(x>=0)reach++;u64 greach;MPI_Allreduce(&reach,&greach,1,MPI_UINT64_T,MPI_SUM,MPI_COMM_WORLD);u64 traversed=o.directed?gscan:gscan/2;double teps=maxelapsed>0?(double)traversed/maxelapsed:0; if(rank==0){std::ostringstream line;line<<o.dataset<<","<<n<<","<<(o.directed?global_m:global_m/2)<<","<<p<<","<<o.ordering<<","<<o.mode<<","<<rep<<","<<sources[rep]<<","<<maxelapsed*1000.0<<","<<traversed<<","<<teps<<","<<greach<<","<<remote<<","<<remote*sizeof(Pair)<<","<<(allvalid?"PASS":"FAIL")<<","<<o.graph_seed<<","<<o.permutation_seed;append_csv(o.summary,"dataset,vertices,edges,ranks,ordering,mode,source_index,source_vertex,elapsed_ms,traversed_edges,teps,reachable_vertices,remote_pairs_sent,remote_payload_bytes,validation,graph_seed,permutation_seed",line.str());for(auto&r:rows){std::ostringstream l;l<<o.dataset<<","<<n<<","<<p<<","<<o.ordering<<","<<o.mode<<","<<rep<<","<<r.level<<","<<r.frontier<<","<<r.expansion_ms<<","<<r.packing_ms<<","<<r.count_exchange_ms<<","<<r.collective_request_ms<<","<<r.localcand_ms<<","<<r.residual_wait_ms<<","<<r.merge_ms<<","<<r.wall_ms<<","<<r.remote<<","<<r.remote*sizeof(Pair)<<","<<r.imbalance;append_csv(o.levels,"dataset,vertices,ranks,ordering,mode,source_index,level,next_frontier,expansion_ms,packing_ms,count_exchange_ms,collective_request_ms,local_candidate_ms,residual_wait_ms,received_merge_ms,level_wall_ms,remote_pairs_sent,remote_payload_bytes,frontier_imbalance",l.str());}}if(!allvalid){if(rank==0)std::cerr<<"BFS validation failed at repetition "<<rep<<"\n";MPI_Abort(MPI_COMM_WORLD,3);}}
 if(rank==0)std::cout<<"Completed dataset="<<o.dataset<<" N="<<n<<" ranks="<<p<<" mode="<<o.mode<<" ordering="<<o.ordering<<" repetitions="<<o.repetitions<<" validation=PASS\n";
 }catch(const std::exception&e){std::cerr<<"Rank "<<rank<<": "<<e.what()<<"\n";MPI_Abort(MPI_COMM_WORLD,1);}MPI_Finalize();return 0;}
