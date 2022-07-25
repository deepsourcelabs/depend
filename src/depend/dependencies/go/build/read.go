package main

/*
#include <stdlib.h>
*/
import "C"
import (
	"encoding/json"
	"unsafe"

	"golang.org/x/mod/modfile"
)

type goMod struct {
	MinGoVer      string
	ModPath       string
	ModVer        string
	ModDeprecated string
	DepVer        []string
}

//export getDepVer
func getDepVer(fptr *C.char) *C.char {
	// Analyzes go.mod contents for Dependency-Analyzer
	//
	// To generate shared libraries:
	// go build -buildmode=c-shared -o <output file>
	//
	// NOTE(SS): Platform dependent shared libraries are present inside
	// "windows", "linux" and "win64" directories (location: ./..)
	file := C.GoString(fptr)
	f, err := modfile.Parse("", []byte(file), nil)
	if err != nil {
		return C.CString("")
	}

	var depVar []string
	for _, dep := range f.Require {
		if len(dep.Mod.Path) > 0 {
			depVar = append(depVar, dep.Mod.Path+";"+dep.Mod.Version)
		}
	}

	var minGoVer, modPath, modVer, modDeprecated string

	if f.Go != nil {
		minGoVer = f.Go.Version
	}

	if f.Module != nil {
		modPath = f.Module.Mod.Path
		modVer = f.Module.Mod.Version
		modDeprecated = f.Module.Deprecated
	}

	retStruct := goMod{
		MinGoVer:      minGoVer,
		ModPath:       modPath,
		ModVer:        modVer,
		ModDeprecated: modDeprecated,
		DepVer:        depVar,
	}

	out, err := json.Marshal(retStruct)
	if err != nil {
		return C.CString("")
	}

	cstr := C.CString(string(out))
	return cstr
}

//export freeCByte
func freeCByte(b unsafe.Pointer) {
	C.free(b)
}

func main() {}
