;------------------------------------------------------------------------------
; NAME:         random.asm
; TYPE:         lib
; DESCRIPTION:  generates pseudo-random numbers
; BUILD:        nasm -f elf -g -F dwarf random.asm -l random.lst
;------------------------------------------------------------------------------ 

section .data
global seed
;seed dd 0b01011110101111101111010010110110
weylk   dd 362437   ; an odd number k to form a weyl sequence
weyls   dd 0        ; current value of the weyl sequence

section .bss
seed    resd 1      ; 32 bit integer

section .text

global init,msquared

;------------------------------------------------------------------------------
; PROCEDURE:    init
; IN:           none
; OUT:          none
; MODIFIES:     seed
; CALLS:        sys_time
; DETAILS:      gets current time, sets seed to that
init:
    pushad          ; save regs
    mov eax,13      ; sys_time
    mov ebx,seed    ; destination
    int 0x80        ; make syscall

    popad           ; restore regs
    ret             ; leave

;------------------------------------------------------------------------------
; PROCEDURE:    msquared
; IN:           none
; OUT:          eax: 32-bit int
; MODIFIES:     eax
; CALLS:        none
; DETAILS:      does middle squared, with weyl sequence
msquared:
    push edx        ; save edx, ebx
    push ebx        

; square
    mov eax,[seed]  ; get seed
    mul eax         ; square seed into edx:eax

; weyl
    mov ebx,dword [weylk]   ; put weyl k into ebx
    add dword [weyls],ebx   ; add weyl k to current weyl value
    add eax,dword [weyls]   ; add current weyl value to squared seed

    mov ax,dx       ; have middle, halves reversed, in eax
    ;ror eax,16      ; swap reversed halves, have middle in eax
    mov [seed],eax  ; put in new seed

    pop ebx         ; restore ebx,edx
    pop edx
    ret
