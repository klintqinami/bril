
function _partition(a: any[], lo: number, hi: number) {
    const p = a[Math.floor((hi + lo) / 2)]

    while (lo <= hi) {
        while (a[lo] < p) {
            lo += 1;
        }

        while (a[hi] > p) {
            hi -= 1;
        }

        if (hi <= lo) {
            return hi;
        }

        const tmp = a[lo]
        a[lo] = a[hi]
        a[hi] = tmp
        lo += 1;
        hi -= 1;
    }

    return hi
}

function _quicksort(a: any[], lo: number, hi: number) {
    if (lo < hi) {
        const k = _partition(a, lo, hi);
        _quicksort(a, lo, k);
        _quicksort(a, k + 1, hi);
    }
}

function quicksort(a: any[]) {
    _quicksort(a, 0, a.length - 1)
}

const len = 10
const b = Array.from({ length: len }, () => Math.floor(Math.random() * len));
console.log("Pre sort")
console.log(b)
console.log("Post sort")
quicksort(b)
console.log(b)