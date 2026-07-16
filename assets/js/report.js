/* 자치구별 요약 리포트 */
(function () {
  'use strict';

  var KINDERGARTENS = window.KINDERGARTENS || [];
  var DATA_META = window.DATA_META || {};

  var KIND_ORDER = ['공립', '사립'];

  var DISTRICT_ORDER = ['강남구', '강동구', '강북구', '강서구', '관악구', '광진구', '구로구',
    '금천구', '노원구', '도봉구', '동대문구', '동작구', '마포구', '서대문구', '서초구',
    '성동구', '성북구', '송파구', '양천구', '영등포구', '용산구', '은평구', '종로구', '중구', '중랑구'];

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function districtColor(d) {
    var idx = DISTRICT_ORDER.indexOf(d);
    if (idx === -1) return '#8D6E63';
    var hue = Math.round((idx * (360 / DISTRICT_ORDER.length)) % 360);
    return 'hsl(' + hue + ', 62%, 50%)';
  }

  function count(list, pred) {
    return list.filter(pred).length;
  }

  /* ---------- 핵심 지표 타일 ---------- */
  var pub = count(KINDERGARTENS, function (f) { return f.kind === '공립'; });
  var priv = count(KINDERGARTENS, function (f) { return f.kind === '사립'; });
  var special = count(KINDERGARTENS, function (f) { return f.hasSpecialClass; });
  var approx = count(KINDERGARTENS, function (f) { return f.geoApprox; });
  var totalStudents = KINDERGARTENS.reduce(function (s, f) { return s + f.studentCount; }, 0);
  var tiles = [
    { num: KINDERGARTENS.length, lbl: '전체 유치원' },
    { num: pub, lbl: '공립' },
    { num: priv, lbl: '사립' },
    { num: special, lbl: '특수학급 운영' },
    { num: totalStudents.toLocaleString(), lbl: '전체 원아 수' },
    { num: approx, lbl: '위치 확인 필요' }
  ];
  document.getElementById('statTiles').innerHTML = tiles.map(function (t) {
    return '<div class="stat-tile"><div class="num">' + t.num + '</div><div class="lbl">' + t.lbl + '</div></div>';
  }).join('');

  /* ---------- 설립 구분 분포 ---------- */
  var kindCounts = {};
  KINDERGARTENS.forEach(function (f) {
    kindCounts[f.kind] = (kindCounts[f.kind] || 0) + 1;
  });
  document.getElementById('kindChips').innerHTML = KIND_ORDER
    .filter(function (k) { return kindCounts[k]; })
    .map(function (k) {
      return '<span class="status-chip"><span class="tag">' + esc(k) + '</span>' +
        '<span class="chip-num">' + kindCounts[k] + '곳</span></span>';
    }).join('');

  /* ---------- 자치구별 막대 차트 ---------- */
  var byDistrict = {};
  KINDERGARTENS.forEach(function (f) {
    (byDistrict[f.district] = byDistrict[f.district] || []).push(f);
  });
  var entries = DISTRICT_ORDER
    .filter(function (d) { return byDistrict[d]; })
    .map(function (d) { return [d, byDistrict[d].length]; });
  entries.sort(function (a, b) { return b[1] - a[1]; });
  var max = entries.length ? entries[0][1] : 1;
  document.getElementById('districtBars').innerHTML = entries.map(function (e) {
    return (
      '<button class="dbar" data-district="' + esc(e[0]) + '" title="지도에서 ' + esc(e[0]) + ' 보기">' +
        '<span>' + esc(e[0]) + '</span>' +
        '<span class="track"><span class="fill" style="width:' + (e[1] / max * 100) + '%; background:' + districtColor(e[0]) + '"></span></span>' +
        '<span class="cnt">' + e[1] + '</span>' +
      '</button>'
    );
  }).join('');

  document.getElementById('districtBars').addEventListener('click', function (e) {
    var dbar = e.target.closest('.dbar');
    if (dbar) {
      location.href = 'index.html?district=' + encodeURIComponent(dbar.getAttribute('data-district'));
    }
  });

  /* ---------- 자치구별 상세 표 ---------- */
  var tbody = document.querySelector('#reportTable tbody');
  tbody.innerHTML = entries.map(function (e) {
    var d = e[0], list = byDistrict[d];
    return (
      '<tr>' +
        '<td><span class="legend-dot" style="background:' + districtColor(d) + '"></span>' + esc(d) + '</td>' +
        '<td>' + list.length + '</td>' +
        '<td>' + count(list, function (f) { return f.kind === '공립'; }) + '</td>' +
        '<td>' + count(list, function (f) { return f.kind === '사립'; }) + '</td>' +
        '<td>' + count(list, function (f) { return f.hasSpecialClass; }) + '</td>' +
      '</tr>'
    );
  }).join('');

  /* ---------- 헤더 ---------- */
  document.getElementById('totalCount').textContent = KINDERGARTENS.length;
  document.getElementById('surveyDate').textContent = DATA_META.surveyDate || '';

  // PWA: 서비스 워커 등록 (홈 화면 설치 · 오프라인 지원)
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('sw.js').catch(function (err) {
        console.warn('서비스 워커 등록 실패:', err);
      });
    });
  }
})();
