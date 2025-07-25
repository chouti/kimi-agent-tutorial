// FizzBuzz程序
// 打印1到15的数字，但：
// - 能被3整除的打印"Fizz"
// - 能被5整除的打印"Buzz"
// - 能被3和5同时整除的打印"FizzBuzz"

function fizzBuzz() {
    for (let i = 1; i <= 50; i++) {
        let output = '';
        
        if (i % 3 === 0) {
            output += 'Fizz';
        }
        
        if (i % 5 === 0) {
            output += 'Buzz';
        }
        
        // 如果output为空，说明既不能被3也不能被5整除，打印数字本身
        console.log(output || i);
    }
}

// 运行FizzBuzz
console.log('FizzBuzz程序开始：');
fizzBuzz();
console.log('程序结束！');

// 导出函数以便在其他模块中使用
module.exports = fizzBuzz;