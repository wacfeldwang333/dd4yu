section .data

; powers of two up to 2^31
two_powers  dd 1,2,4,8,16,32,64,128,256,512,1024,2048,4096,8192,16384,32768,65536,131072,262144,524288,1048576,2097152,4194304,8388608,16777216,33554432,67108864,134217728,268435456,536870912,1073741824,2147483648

section .text
global bin_str

;------------------------------------------------------------------------------
; PROCEDURE:    bin_str
; IN:           eax: dword binary number, ebx: address of 32 bytes
; OUT:          memory at ebx: 32 bit equivalent number
; MODIFIES:     none
; CALLS:        none
; DETAILS:      checks each bit, then writes corresponding ascii 0 or 1 
bin_str:
        pushad      ; save regs
        
        mov ecx,31  ; set bit counter to least significant bit
shift:  shr eax,1   ; shift rightmost bit into carry flag
        jc .one     ; if bit is 1, jump

.zer:   mov byte [ebx+ecx],48   ; write ASCII 0 to next byte
        jmp .cloop              ; jump to loop check
.one    mov byte [ebx+ecx],49   ;write ASCII 1
        jmp .cloop              ; jump to loop check

.cloop: dec ecx                 ; dec bit counter
        cmp ecx,0               ; compare bit counter with 0
        jge shift               ; if (signed) greater, equal 0, loop

        popad       ; restore regs
        ret
