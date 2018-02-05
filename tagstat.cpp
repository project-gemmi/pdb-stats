// Copyright 2018 Global Phasing Ltd.

#include "gemmi/cif.hpp"
#include "gemmi/dirwalk.hpp"  // for CifWalk
#include "gemmi/gz.hpp"  // for MaybeGzipped
#include <cstdio>  // for printf
#include <utility>  // for pair
#include <string>
#include <map>
#include <vector>

namespace pegtl = tao::pegtl;
namespace cif = gemmi::cif;
namespace rules = gemmi::cif::rules;

struct TagStats {
  int block_count = 0;
  size_t total_count = 0;
  int min_count = INT_MAX;
  int max_count = 1;
};

struct Context {
  std::map<std::string, TagStats> stats;
  int total_blocks = 0;
  std::string tag;
  std::vector<std::pair<std::string, int>> loop_info;
  size_t column = 0;
};

template<typename Rule> struct Counter : pegtl::nothing<Rule> {};

template<> struct Counter<rules::datablockname> {
  template<typename Input> static void apply(const Input&, Context& ctx) {
    ctx.total_blocks++;
  }
};
template<> struct Counter<rules::str_global> {
  template<typename Input> static void apply(const Input& in, Context& ctx) {
    Counter<rules::datablockname>::apply(in, ctx);
  }
};

template<> struct Counter<rules::tag> {
  template<typename Input> static void apply(const Input& in, Context& ctx) {
    ctx.tag = in.string();
  }
};
template<> struct Counter<rules::value> {
  template<typename Input> static void apply(const Input& in, Context& ctx) {
    if (!cif::is_null(in.string())) {
      TagStats& st = ctx.stats[ctx.tag];
      st.block_count++;
      st.total_count++;
      st.min_count = 1;
    }
    ctx.tag = "";
  }
};

template<> struct Counter<rules::loop_tag> {
  template<typename Input> static void apply(const Input& in, Context& ctx) {
    ctx.loop_info.push_back({in.string(), 0});
  }
};
template<> struct Counter<rules::loop_value> {
  template<typename Input> static void apply(const Input& in, Context& ctx) {
    if (!cif::is_null(in.string()))
      ctx.loop_info[ctx.column].second++;
    ctx.column++;
    if (ctx.column == ctx.loop_info.size())
      ctx.column = 0;
  }
};
template<> struct Counter<rules::loop_end> {
  template<typename Input> static void apply(const Input&, Context& ctx) {
    for (auto& info : ctx.loop_info) {
      TagStats& st = ctx.stats[info.first];
      if (int n = info.second) {
        st.block_count++;
        st.total_count += n;
        st.max_count = std::max(st.max_count, n);
        st.min_count = std::min(st.min_count, n);
      }
    }
    ctx.column = 0;
    ctx.loop_info.clear();
  }
};

int main(int argc, char **argv) {
  size_t file_count = 0;
  Context ctx;
  for (int i = 1; i < argc; ++i) {
    try {
      for (const char* path : gemmi::CifWalk(argv[i])) {
        gemmi::MaybeGzipped input(path);
        if (input.is_stdin()) {
          pegtl::cstream_input<> in(stdin, 16*1024, "stdin");
          pegtl::parse<rules::file, Counter, cif::Errors>(in, ctx);
        } else if (input.is_compressed()) {
          std::unique_ptr<char[]> mem = input.memory();
          pegtl::memory_input<> in(mem.get(), input.mem_size(), path);
          pegtl::parse<rules::file, Counter, cif::Errors>(in, ctx);
        } else {
          pegtl::file_input<> in(path);
          pegtl::parse<rules::file, Counter, cif::Errors>(in, ctx);
        }
        file_count++;
      }
    } catch (std::runtime_error &e) {
      fprintf(stderr, "Error: %s\n", e.what());
      return 2;
    }
  }
  for (auto& item : ctx.stats) {
    TagStats& st = item.second;
    if (st.block_count == 0)
      continue;
    double avg = double(st.total_count) / st.block_count;
    std::printf("%-45s %7.3f%% %5d %5d %5.2f\n",
        item.first.c_str(), 100.0 * st.block_count / ctx.total_blocks,
        st.min_count, st.max_count, avg);
  }
  std::printf("Block count: %d\n", ctx.total_blocks);
  std::printf("File count: %zu\n", file_count);
  return 0;
}

// vim:sw=2:ts=2:et
